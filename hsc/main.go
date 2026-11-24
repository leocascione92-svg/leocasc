// Home Server Connect 0.1.1 — Windows 7 portable prototype.
// Nonofficial Tailscale client. Uses unsupported Tailscale v1.44.3.
// Ephemeral credentials, no TUN driver, only 127.0.0.1 listeners.
package main

import (
 "context"
 "crypto/ecdsa"
 "crypto/elliptic"
 "crypto/rand"
 "crypto/sha256"
 "crypto/tls"
 "crypto/x509"
 "crypto/x509/pkix"
 _ "embed"
 "encoding/hex"
 "encoding/json"
 "encoding/pem"
 "errors"
 "flag"
 "fmt"
 "log"
 "math/big"
 "net"
 "net/http"
 "net/http/httputil"
 "net/netip"
 "net/url"
 "os"
 "os/exec"
 "os/signal"
 "regexp"
 "runtime"
 "strings"
 "sync"
 "syscall"
 "time"
 "tailscale.com/ipn/store/mem"
 "tailscale.com/tsnet"
)

//go:embed panel.html
var html string
var authRegex=regexp.MustCompile("https://login[.]tailscale[.]com/a/[A-Za-z0-9_-]+")
type app struct{
 mu sync.RWMutex
 status, message, authURL, observed, pin, ip, token, portal, localFingerprint string
 ts *tsnet.Server
 target *url.URL
 stop chan struct{}
 once sync.Once
}
func(a *app) set(state, message string){a.mu.Lock();a.status=state;a.message=message;a.mu.Unlock()}
func(a *app) auth(s string){a.mu.Lock();a.authURL=s;a.status="login";a.message="Apri l'autenticazione Tailscale";a.mu.Unlock()}
func(a *app) snapshot()map[string]interface{}{a.mu.RLock();defer a.mu.RUnlock();return map[string]interface{}{"status":a.status,"message":a.message,"authURL":a.authURL,"ip":a.ip,"observed":a.observed,"pinned":a.pin!="","portal":a.portal,"localFingerprint":a.localFingerprint}}
func randomBytes(n int)([]byte,error){b:=make([]byte,n);_,err:=rand.Read(b);return b,err}
func cert()(tls.Certificate,string,error){
 k,e:=ecdsa.GenerateKey(elliptic.P256(),rand.Reader);if e!=nil{return tls.Certificate{},"",e}
 rb,e:=randomBytes(16);if e!=nil{return tls.Certificate{},"",e}
 t:=&x509.Certificate{SerialNumber:new(big.Int).SetBytes(rb),Subject:pkix.Name{CommonName:"Home Server Connect - local only"},NotBefore:time.Now().Add(-time.Hour),NotAfter:time.Now().Add(24*time.Hour),KeyUsage:x509.KeyUsageDigitalSignature,ExtKeyUsage:[]x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},IPAddresses:[]net.IP{net.ParseIP("127.0.0.1")},DNSNames:[]string{"localhost"},BasicConstraintsValid:true}
 der,e:=x509.CreateCertificate(rand.Reader,t,t,&k.PublicKey,k);if e!=nil{return tls.Certificate{},"",e}
 key,e:=x509.MarshalECPrivateKey(k);if e!=nil{return tls.Certificate{},"",e}
 c,e:=tls.X509KeyPair(pem.EncodeToMemory(&pem.Block{Type:"CERTIFICATE",Bytes:der}),pem.EncodeToMemory(&pem.Block{Type:"EC PRIVATE KEY",Bytes:key}))
 h:=sha256.Sum256(der);return c,strings.ToUpper(hex.EncodeToString(h[:])),e
}
func fp(b []byte)string{h:=sha256.Sum256(b);return strings.ToUpper(hex.EncodeToString(h[:]))}
func normalized(s string)string{return strings.ToUpper(strings.ReplaceAll(strings.ReplaceAll(strings.TrimSpace(s),":","")," ",""))}
func(a *app) fingerprint(ctx context.Context)(string,error){
 c,e:=a.ts.Dial(ctx,"tcp",a.target.Host);if e!=nil{return "",e};defer c.Close()
 t:=tls.Client(c,&tls.Config{MinVersion:tls.VersionTLS12,InsecureSkipVerify:true}) // only obtain fingerprint; independently verified by the user
 if e=t.HandshakeContext(ctx);e!=nil{return "",e}
 cs:=t.ConnectionState();if len(cs.PeerCertificates)<1{return "",errors.New("certificato mancante")}
 return fp(cs.PeerCertificates[0].Raw),nil
}
func(a *app) admin(host string, control string)bool{return host==control || host=="localhost:"+strings.Split(control,":")[1]}
func(a *app) controller(control string)http.Handler{
 mux:=http.NewServeMux()
 mux.HandleFunc("/",func(w http.ResponseWriter,r *http.Request){
 if !a.admin(r.Host,control){http.Error(w,"Host non autorizzato",403);return}
 if r.URL.Path!="/"{http.NotFound(w,r);return}
 w.Header().Set("Content-Type","text/html; charset=utf-8");w.Header().Set("Cache-Control","no-store")
 w.Header().Set("Content-Security-Policy","default-src 'none'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'none'; base-uri 'none'")
 w.Header().Set("Referrer-Policy","no-referrer")
 _,_=w.Write([]byte(strings.ReplaceAll(html,"__TOKEN__",a.token)))
 })
 mux.HandleFunc("/api/status",func(w http.ResponseWriter,r *http.Request){
 if !a.admin(r.Host,control){http.Error(w,"Host non autorizzato",403);return}
 w.Header().Set("Cache-Control","no-store");w.Header().Set("Content-Type","application/json")
 _=json.NewEncoder(w).Encode(a.snapshot())
 })
 authPost:=func(w http.ResponseWriter,r *http.Request)bool{
 if !a.admin(r.Host,control) || r.Method!="POST" || r.Header.Get("X-Connect-Token")!=a.token || (r.Header.Get("Origin")!=""&&r.Header.Get("Origin")!="http://"+r.Host){http.Error(w,"Richiesta non consentita",403);return false};return true
 }
 mux.HandleFunc("/api/cert",func(w http.ResponseWriter,r *http.Request){
 if !authPost(w,r){return}
 a.mu.RLock();ok:=a.status=="connected";a.mu.RUnlock()
 if !ok{http.Error(w,"Prima collegati a Tailscale",409);return}
 ctx,cancel:=context.WithTimeout(r.Context(),12*time.Second);defer cancel()
 v,e:=a.fingerprint(ctx);if e!=nil{http.Error(w,"Server non raggiungibile",502);return}
 a.mu.Lock();a.observed=v;a.pin="";a.mu.Unlock()
 w.Header().Set("Content-Type","application/json");_=json.NewEncoder(w).Encode(map[string]string{"fingerprint":v})
 })
 mux.HandleFunc("/api/pin",func(w http.ResponseWriter,r *http.Request){
 if !authPost(w,r){return}
 r.Body=http.MaxBytesReader(w,r.Body,512);defer r.Body.Close()
 var v struct{Fingerprint string}
 if e:=json.NewDecoder(r.Body).Decode(&v);e!=nil{http.Error(w,"Dati invalidi",400);return}
 p:=normalized(v.Fingerprint)
 a.mu.Lock()
 if len(p)!=64 || p!=a.observed{a.mu.Unlock();http.Error(w,"Impronta non corrispondente",409);return}
 a.pin=p;a.mu.Unlock()
 w.Header().Set("Content-Type","application/json");_,_=w.Write([]byte("{\"ok\":true}"))
 })
 mux.HandleFunc("/api/stop",func(w http.ResponseWriter,r *http.Request){
 if !authPost(w,r){return};_,_=w.Write([]byte("Chiusura"));a.once.Do(func(){close(a.stop)})
 })
 return mux
}
func(a *app) gateway(proxyAddr string)http.Handler{
 rp:=httputil.NewSingleHostReverseProxy(a.target)
 rp.Transport=&http.Transport{
 DialContext:a.ts.Dial,TLSHandshakeTimeout:10*time.Second,
 TLSClientConfig:&tls.Config{MinVersion:tls.VersionTLS12,InsecureSkipVerify:true,
 VerifyPeerCertificate:func(raw [][]byte,_ [][]*x509.Certificate)error{
 if len(raw)==0{return errors.New("nessun certificato")}
 a.mu.RLock();p:=a.pin;a.mu.RUnlock()
 if p=="" || fp(raw[0])!=p{return errors.New("pin TLS errato o assente")};return nil
 }},
 }
 old:=rp.Director;rp.Director=func(req *http.Request){
 old(req);req.Host=a.target.Host;req.Header.Del("Proxy-Authorization");req.Header.Del("Forwarded")
 req.Header.Del("X-Forwarded-For");req.Header.Del("X-Forwarded-Host")
 req.Header.Set("X-Forwarded-Proto","https")
 if req.Header.Get("Origin")!=""{req.Header.Set("Origin",a.target.Scheme+"://"+a.target.Host)}
 }
 rp.ModifyResponse=func(resp *http.Response)error{
 if loc:=resp.Header.Get("Location");loc!=""{
 u,e:=url.Parse(loc);if e==nil && u.IsAbs() && u.Host==a.target.Host{u.Scheme="https";u.Host=proxyAddr;resp.Header.Set("Location",u.String())}
 }
 resp.Header.Set("Cache-Control","no-store");return nil
 }
 rp.ErrorHandler=func(w http.ResponseWriter,_ *http.Request,_ error){http.Error(w,"Server S21 non disponibile o certificato non verificato",502)}
 return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
 a.mu.RLock();p:=a.pin;a.mu.RUnlock()
 if p==""{http.Error(w,"Verifica il certificato del Galaxy S21 nel pannello di controllo",403);return}
 if r.Host!=proxyAddr&&r.Host!="localhost:"+strings.Split(proxyAddr,":")[1]{http.Error(w,"Host non autorizzato",403);return}
 rp.ServeHTTP(w,r)
 })
}
func browse(s string){if runtime.GOOS!="windows"{return};c:=exec.Command("rundll32.exe","url.dll,FileProtocolHandler",s);if e:=c.Start();e!=nil{log.Printf("Apri manualmente %s",s)}else{go func(){_=c.Wait()}()}}
func run()error{
 server:=flag.String("server","100.106.100.13:8765","Indirizzo Tailscale S21:porta")
 flag.Parse();ap,e:=netip.ParseAddrPort(*server)
 if e!=nil||!ap.Addr().Is4()||!netip.MustParsePrefix("100.64.0.0/10").Contains(ap.Addr())||ap.Port()==0{return errors.New("indirizzo Tailscale non valido")}
 t,_:=url.Parse("https://"+*server)
 c,localFP,e:=cert();if e!=nil{return e}
 secret,e:=randomBytes(32);if e!=nil{return e}
 tmp,e:=os.MkdirTemp("","hsc-temporary-");if e!=nil{return e};defer os.RemoveAll(tmp)
 ctx,cancel:=signal.NotifyContext(context.Background(),os.Interrupt,syscall.SIGTERM);defer cancel()
 a:=&app{status:"starting",message:"Avvio Tailscale",target:t,token:hex.EncodeToString(secret),localFingerprint:localFP,stop:make(chan struct{})}
 a.ts=&tsnet.Server{Dir:tmp,Store:new(mem.Store),Ephemeral:true,Hostname:"homeserver-connect",Logf:func(format string,args ...interface{}){
 s:=fmt.Sprintf(format,args...);if u:=authRegex.FindString(s);u!=""{a.auth(u)}
 }}
 cl,e:=net.Listen("tcp","127.0.0.1:0");if e!=nil{return e};defer cl.Close()
 pl,e:=net.Listen("tcp","127.0.0.1:0");if e!=nil{return e};defer pl.Close()
 control:=cl.Addr().String();portal:=pl.Addr().String();a.portal="https://"+portal+"/"
 cs:=&http.Server{Handler:a.controller(control),ReadHeaderTimeout:6*time.Second}
 ps:=&http.Server{Handler:a.gateway(portal),ReadHeaderTimeout:6*time.Second,TLSConfig:&tls.Config{MinVersion:tls.VersionTLS12,Certificates:[]tls.Certificate{c}}}
 go func(){if e:=cs.Serve(cl);e!=nil&&e!=http.ErrServerClosed{log.Print(e);a.once.Do(func(){close(a.stop)})}}()
 go func(){if e:=ps.ServeTLS(pl,"","");e!=nil&&e!=http.ErrServerClosed{log.Print(e);a.once.Do(func(){close(a.stop)})}}()
 go func(){
 a.set("connecting","Connessione a Tailscale in corso")
 s,e:=a.ts.Up(ctx)
 if e!=nil{if ctx.Err()==nil{a.set("error","Login/connessione falliti: client storico da verificare");log.Print(e)};return}
 ip:="";if s!=nil&&len(s.TailscaleIPs)>0{ip=s.TailscaleIPs[0].String()}
 a.mu.Lock();a.status="connected";a.message="Connessione privata attiva";a.ip=ip;a.mu.Unlock()
 }()
 page:="http://"+control+"/"
 fmt.Println("Home Server Connect 0.1.1 - sperimentale Windows 7")
 fmt.Println("Controllo:",page);fmt.Println("Nessuna chiave Tailscale salvata sulla USB; non usare su PC non fidati.")
 browse(page)
 select{case <-ctx.Done():case <-a.stop:}
 cancel();shutdownCtx,stop:=context.WithTimeout(context.Background(),5*time.Second);defer stop()
 _=cs.Shutdown(shutdownCtx);_=ps.Shutdown(shutdownCtx);_=a.ts.Close();return nil
}
func main(){if e:=run();e!=nil{fmt.Println("ERRORE:",e);fmt.Println("Premi invio...");fmt.Scanln()}}
