import {refundReviewLabel} from "../lib/paymentHistory";
import {useEffect,useRef,useState} from "react";
import {accountResponse,useAccount} from "../hooks/useAccount";
import "./payments.css";

type Package={id:string;amount:number;credits:number;currency:string};
type Receipt={id:string;mode:"live";status:string;amount:number;credits:number;currency:string;qr_image_url:string|null;expires_at:number|null;refund_status?:string|null;refund_eligibility?:string};
const price=(amount:number)=>`₱${(amount/100).toFixed(2)}`;
const savedKey="arena-live-attempt";
const statusLabel=(status:string)=>({creating:"Creating QR",creation_failed:"Needs checking",pending:"Pending",paid:"Paid",failed:"Failed",expired:"Expired"})[status]??"Needs checking";
const refundLabel=(status:string)=>({succeeded:"Refund processed",held:"Refund under review",failed:"Refund failed"})[status]??"Refund needs checking";
function purchaseDate(timestamp?:number){
 return timestamp&&Number.isFinite(timestamp)?new Date(timestamp*1000).toLocaleString(undefined,{month:"short",day:"numeric",year:"numeric",hour:"numeric",minute:"2-digit"}):"Date unavailable";
}
function receipt(value:Receipt,expected?:string):Receipt {
 if(!value||value.mode!=="live"||typeof value.id!=="string"||!value.id||(expected&&expected!==value.id)
  ||!Number.isSafeInteger(value.amount)||value.amount<=0||!Number.isSafeInteger(value.credits)||value.credits<=0||value.currency!=="PHP"
  ||!["creating","creation_failed","pending","paid","failed","expired"].includes(value.status)
  ||(value.qr_image_url!==null&&(typeof value.qr_image_url!=="string"||!/^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(value.qr_image_url)))
  ||(value.status==="pending"&&(!value.qr_image_url||!Number.isSafeInteger(value.expires_at))))throw new Error("The purchase could not be verified. Keep this attempt and check history.");
 return value;
}
export function LivePaymentPage(){
 const {account,refresh,error:accountError}=useAccount(false);
 const [packages,setPackages]=useState<Package[]>([]),[enabled,setEnabled]=useState(false),[support,setSupport]=useState("");
 const [selected,setSelected]=useState(""),[topup,setTopup]=useState<Receipt|null>(null),[hidden,setHidden]=useState(false);
 const [error,setError]=useState(""),[busy,setBusy]=useState(false),[now,setNow]=useState(Date.now());
 const [retained,setRetained]=useState(false);
 const [openingReceipt,setOpeningReceipt]=useState(false);
 const paymentPanel=useRef<HTMLElement>(null);
 const pending=useRef(false),owner=useRef<string|undefined>(),epoch=useRef(0);
 useEffect(()=>{let active=true;void fetch("/api/payments/live/config",{cache:"no-store"}).then(accountResponse).then(body=>{
  if(!active)return;const catalog:Package[]=Array.isArray(body.packages)?body.packages.filter((p:Package)=>p&&typeof p.id==="string"&&p.currency==="PHP"&&Number.isSafeInteger(p.amount)&&p.amount>0&&Number.isSafeInteger(p.credits)&&p.credits>0):[];
  setPackages(catalog);setSelected(previous=>previous||catalog[0]?.id||"");setEnabled(body.mode==="live"&&body.enabled===true&&catalog.length>0);setSupport(typeof body.support_email==="string"?body.support_email:"");
 }).catch(()=>{if(active)setError("Top-ups are temporarily unavailable.");});return()=>{active=false;};},[]);
 useEffect(()=>{if(owner.current!==account?.user?.id){owner.current=account?.user?.id;epoch.current++;setTopup(null);setHidden(false);setError("");setRetained(false);
  try{const saved=JSON.parse(sessionStorage.getItem(savedKey)??"null");if(saved?.owner===account?.user?.id&&saved?.key){setRetained(true);setSelected(saved.package);}}catch{/* No valid saved attempt. */}
 }},[account?.user?.id]);
 useEffect(()=>{if(!account?.authenticated||!account.user)return;
  let active=true,reading=false;const expected=account.user.id;
  async function update(){if(reading||pending.current)return;reading=true;const version=epoch.current;
   try{const stored=JSON.parse(sessionStorage.getItem(savedKey)??"null");const id=topup?.id??(stored?.owner===expected?stored.receipt:null);
    if(!id)return;const body=await accountResponse(await fetch(`/api/payments/live/topups/${encodeURIComponent(id)}`,{cache:"no-store"}));
    if(!active||epoch.current!==version)return;const checked=receipt(body.topup,id);setTopup(checked);setError("");if(checked.status==="paid")await refresh();
   }catch{if(active&&epoch.current===version)setError("Could not refresh your purchase. Its receipt is retained; try again.");}finally{reading=false;}}
  if(!topup)void update();const timer=window.setInterval(()=>{setNow(Date.now());void update();},5000);
  const resume=()=>{setNow(Date.now());void refresh();void update();};window.addEventListener("focus",resume);window.addEventListener("defense-native-resume",resume);
  return()=>{active=false;window.clearInterval(timer);window.removeEventListener("focus",resume);window.removeEventListener("defense-native-resume",resume);};
 },[account?.user?.id,account?.authenticated,topup?.id,refresh]);
 useEffect(()=>{const tick=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(tick);},[]);
 async function create(){if(pending.current||!account?.user||!account.csrf_token)return;
  pending.current=true;setBusy(true);setError("");const version=epoch.current;
  try{let saved;try{saved=JSON.parse(sessionStorage.getItem(savedKey)??"null");}catch{saved=null;}
   if(saved?.owner===account.user.id&&saved?.receipt){
    setOpeningReceipt(true);
    const restored=await accountResponse(await fetchResponse(saved.receipt));
    if(epoch.current===version){setTopup(receipt(restored.topup,saved.receipt));paymentPanel.current?.focus();}
    return;
   }
   const attempt=saved?.owner===account.user.id&&saved?.key?saved:{owner:account.user.id,key:crypto.randomUUID(),package:selected};
   setRetained(true);setSelected(attempt.package);
   sessionStorage.setItem(savedKey,JSON.stringify(attempt));
   const body=await accountResponse(await fetch("/api/payments/live/topups",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":account.csrf_token,"Idempotency-Key":attempt.key},body:JSON.stringify({package_id:attempt.package})}));
   if(epoch.current!==version)return;const checked=receipt(body.topup);const pack=packages.find(p=>p.id===attempt.package);
   if(!pack||pack.amount!==checked.amount||pack.credits!==checked.credits)throw new Error("The purchase differs from the selected package. Check history.");
   sessionStorage.setItem(savedKey,JSON.stringify({...attempt,receipt:checked.id}));setTopup(checked);setHidden(false);paymentPanel.current?.focus();await refresh();
  }catch(failure){if(epoch.current===version)setError(failure instanceof Error?failure.message:"The purchase could not be created.");}
  finally{pending.current=false;setBusy(false);setOpeningReceipt(false);}}
 async function openReceipt(id:string){
  if(pending.current||!account?.user)return;
  const version=++epoch.current;
  pending.current=true;setBusy(true);setOpeningReceipt(true);setError("");setHidden(false);setTopup(null);
  sessionStorage.setItem(savedKey,JSON.stringify({owner:account.user.id,receipt:id}));setRetained(true);
  try{const body=await accountResponse(await fetchResponse(id));if(epoch.current===version){setTopup(receipt(body.topup,id));paymentPanel.current?.focus();}}
  catch{if(epoch.current===version)setError("Could not open the receipt. Retry to check this purchase.");}
  finally{pending.current=false;setBusy(false);setOpeningReceipt(false);}
 }
 function newPurchase(){if(pending.current)return;epoch.current++;sessionStorage.removeItem(savedKey);setTopup(null);setHidden(false);setError("");setRetained(false);}
 const remaining=Math.max(0,Math.ceil(((topup?.expires_at??0)*1000-now)/1000));
 const available=account?.authenticated&&account.topup_invited&&enabled;
 const qrAvailable=topup?.status==="pending"&&remaining>0;
 return <main className="payment-page live-payment-page"><div className="payment-container">
  <header className="payment-header"><a className="payment-back" href="/?account=1">← Back to your room</a><div className="payment-title"><div><span className="payment-eyebrow">ACCOUNT / PAYMENTS</span><h1>Credits & purchases</h1><p>Everything you need for your next defense.</p></div>{support&&<a className="payment-support" href={`mailto:${encodeURIComponent(support)}?subject=${encodeURIComponent(`Payment support${topup?` · ${topup.id}`:""}`)}`}>Payment support <span aria-hidden="true">↗</span></a>}</div></header>
  {!account?<p role="status">Loading your account…</p>:!account.authenticated?<section className="payment-account"><h2>Sign in to view your credits</h2>{account.google_enabled?<a className="button-primary payment-login" href="/api/auth/google/login?return_to=%2F%3Fpayments%3Dlive">Sign in with Google</a>:<p>Sign-in is temporarily unavailable.</p>}</section>:<>
   <section className="payment-account payment-wallet" aria-label="Credit balance"><div><span className="payment-eyebrow">AVAILABLE CREDITS</span><p className="payment-balance"><b>{account.live_credits??0}</b><span>credits</span></p><p>{account.live_reserved_credits??0} reserved · {account.user?.name}</p></div><div className="payment-wallet-detail"><p><b>10 credits per defense</b><br/>Questions and coaching included</p><button className="button-secondary" onClick={()=>{void refresh();}}>Refresh balance</button></div></section>
   <div className="payment-columns"><section ref={paymentPanel} tabIndex={-1} className="payment-account payment-package" aria-labelledby="add-credits-title" aria-busy={busy}><div><h2 id="add-credits-title">{topup?"Your payment":"Add credits"}</h2><p className="payment-muted">Temporary rate · ₱1 = 10 credits · No expiry</p></div>
    {!available&&<p>Top-ups are temporarily unavailable for your account. Voucher access remains available in Account.</p>}
    {openingReceipt?<p role="status">Opening your receipt…</p>:!topup&&<><fieldset className="payment-packages" disabled={busy||retained}><legend>Credit package</legend><div className="payment-package-options">{packages.map(p=><label className={`payment-option${selected===p.id?" is-selected":""}`} key={p.id}><input type="radio" name="live-package" value={p.id} checked={selected===p.id} onChange={()=>setSelected(p.id)}/><span><strong>{price(p.amount)}</strong><span>{p.credits} credits</span></span></label>)}</div></fieldset>
     {retained&&<p>A purchase attempt is retained. Retry uses the original package.</p>}
     <button className="button-primary" disabled={busy||(!available&&!retained)} onClick={()=>{void create();}}>{busy?"Creating your QR…":retained?"Retry purchase":`Pay ${price(packages.find(p=>p.id===selected)?.amount??0)}`}</button><p className="payment-muted payment-provider">Secure QR Ph payment via PayMongo</p></>}
    {topup&&<div className="payment-receipt"><h3>{price(topup.amount)} · {topup.credits} credits</h3>
     <p role="status" className="payment-receipt-status">{topup.status==="paid"?`Payment received · ${topup.credits} credits added`:topup.status==="pending"?(remaining>0?"Waiting for payment":"QR time elapsed · checking payment status"):topup.status==="creation_failed"?"QR creation unverified · check history before starting again":topup.status==="creating"?"Creating your QR…":`Payment ${topup.status}`}</p>
     {qrAvailable&&!hidden&&<div className="payment-qr-area"><img className="payment-qr" src={topup.qr_image_url??""} alt="Payment QR Ph code"/><p>Scan with GCash or a QR Ph wallet</p><p className="payment-qr-expiry">Expires in <time>{String(Math.floor(remaining/60)).padStart(2,"0")}:{String(remaining%60).padStart(2,"0")}</time></p><a className="button-primary payment-download" href={topup.qr_image_url??""} download={`payment-qr-${topup.id.replace(/[^a-zA-Z0-9_-]/g,"_")}.png`}>Download QR code <span aria-hidden="true">↓</span></a></div>}
     {qrAvailable&&<button className="button-secondary" onClick={()=>setHidden(!hidden)}>{hidden?"Show QR":"Hide QR"}</button>}
     {hidden&&<p>This hides the QR on this device. It does not cancel the payment.</p>}
     {["paid","failed","expired"].includes(topup.status)&&<button className="button-secondary" disabled={busy} onClick={newPurchase}>Start another top-up</button>}
     <details className="payment-receipt-details"><summary>Receipt details</summary><p className="payment-order">Receipt: {topup.id}</p>{topup.refund_status&&<p>{refundLabel(topup.refund_status)}</p>}<p>{refundReviewLabel(topup.refund_eligibility)}</p></details></div>}
   </section>
   <section className="payment-account payment-purchases" aria-labelledby="purchase-title"><div className="payment-section-heading"><h2 id="purchase-title">Your purchases</h2><span className="payment-muted">Latest {account.live_orders?.length??0}</span></div>{account.live_orders?.length?<ul className="payment-purchase-list">{account.live_orders.map(order=><li className="payment-purchase" key={order.id}><div className="payment-purchase-top"><strong>{price(order.amount)}</strong><span className={`payment-status payment-status-${order.status}`}>{statusLabel(order.status)}</span></div><p className="payment-purchase-meta"><span>{order.credits} credits</span><time dateTime={order.created_at?new Date(order.created_at*1000).toISOString():undefined}>{purchaseDate(order.created_at)}</time></p>{order.refund_status&&<p className="payment-muted">{refundLabel(order.refund_status)}</p>}<div className="payment-purchase-bottom"><span className="payment-short-reference" title={order.id}>…{order.id.slice(-10)}</span><button className="payment-receipt-link" disabled={busy} aria-label={`View receipt ${order.id}`} onClick={()=>{void openReceipt(order.id);}}>View receipt <span aria-hidden="true">↗</span></button></div></li>)}</ul>:<div className="payment-empty"><p>No purchases yet</p><p className="payment-muted">Your top-ups and receipts will appear here.</p></div>}</section></div>
  </>}
  {(error||accountError)&&<p role="alert" className="payment-error">{error||accountError}</p>}
 </div></main>;
}
async function fetchResponse(id:string){return fetch(`/api/payments/live/topups/${encodeURIComponent(id)}`,{cache:"no-store"});}
