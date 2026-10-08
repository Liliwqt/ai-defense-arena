import {refundReviewLabel} from "../lib/paymentHistory";
import {useEffect,useRef,useState} from "react";
import {accountResponse,useAccount} from "../hooks/useAccount";
import "./payments.css";

type Package={id:string;amount:number;credits:number;currency:string};
type Receipt={id:string;mode:"live";status:string;amount:number;credits:number;currency:string;qr_image_url:string|null;expires_at:number|null;refund_status?:string|null;refund_eligibility?:string};
const price=(amount:number)=>`₱${(amount/100).toFixed(2)}`;
const savedKey="arena-live-attempt";
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
  void update();const timer=window.setInterval(()=>{setNow(Date.now());void update();},5000);
  const resume=()=>{setNow(Date.now());void refresh();void update();};window.addEventListener("focus",resume);window.addEventListener("defense-native-resume",resume);
  return()=>{active=false;window.clearInterval(timer);window.removeEventListener("focus",resume);window.removeEventListener("defense-native-resume",resume);};
 },[account?.user?.id,account?.authenticated,topup?.id,refresh]);
 useEffect(()=>{const tick=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(tick);},[]);
 async function create(){if(pending.current||!account?.user||!account.csrf_token)return;
  pending.current=true;setBusy(true);setError("");const version=epoch.current;
  try{let saved;try{saved=JSON.parse(sessionStorage.getItem(savedKey)??"null");}catch{saved=null;}
   if(saved?.owner===account.user.id&&saved?.receipt){
    const restored=await accountResponse(await fetchResponse(saved.receipt));
    if(epoch.current===version)setTopup(receipt(restored.topup,saved.receipt));
    return;
   }
   const attempt=saved?.owner===account.user.id&&saved?.key?saved:{owner:account.user.id,key:crypto.randomUUID(),package:selected};
   setRetained(true);setSelected(attempt.package);
   sessionStorage.setItem(savedKey,JSON.stringify(attempt));
   const body=await accountResponse(await fetch("/api/payments/live/topups",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":account.csrf_token,"Idempotency-Key":attempt.key},body:JSON.stringify({package_id:attempt.package})}));
   if(epoch.current!==version)return;const checked=receipt(body.topup);const pack=packages.find(p=>p.id===attempt.package);
   if(!pack||pack.amount!==checked.amount||pack.credits!==checked.credits)throw new Error("The purchase differs from the selected package. Check history.");
   sessionStorage.setItem(savedKey,JSON.stringify({...attempt,receipt:checked.id}));setTopup(checked);setHidden(false);await refresh();
  }catch(failure){if(epoch.current===version)setError(failure instanceof Error?failure.message:"The purchase could not be created.");}
  finally{pending.current=false;setBusy(false);}}
 function newPurchase(){epoch.current++;sessionStorage.removeItem(savedKey);setTopup(null);setHidden(false);setError("");setRetained(false);}
 const remaining=Math.max(0,Math.ceil(((topup?.expires_at??0)*1000-now)/1000));
 const available=account?.authenticated&&account.topup_invited&&enabled;
 return <main className="payment-page"><div className="payment-container">
  <header className="payment-header"><h1>Top up credits</h1><a className="payment-back" href="/?account=1">Return to your room</a></header>
  {!account?.authenticated?<section><h2>Sign in to view your credits</h2>{account?.google_enabled?<a className="button-primary" href="/api/auth/google/login?return_to=%2F%3Fpayments%3Dlive">Sign in with Google</a>:<p>Sign-in is temporarily unavailable.</p>}</section>:<>
   <section className="payment-account"><h2>{account.user?.name}</h2><p className="payment-balance"><b>{account.live_credits??0}</b> available credits · {account.live_reserved_credits??0} reserved</p><p>10 credits per defense · Questions and coaching included</p>
    <button className="button-secondary" onClick={()=>{void refresh();}}>Refresh balance</button></section>
   <section className="payment-account payment-package"><h2>Add credits</h2><p>Temporary rate · ₱1 = 10 credits · Credits do not expire</p>
    {!available&&<p>Top-ups are temporarily unavailable for your account. Voucher access remains available in Account.</p>}
    {!topup&&<><label htmlFor="live-package">Credit package</label><select id="live-package" value={selected} disabled={busy||retained} onChange={e=>setSelected(e.target.value)}>{packages.map(p=><option key={p.id} value={p.id}>{price(p.amount)} · {p.credits} credits</option>)}</select>
     {retained&&<p>A purchase attempt is retained. Retry uses the original package.</p>}
     <button className="button-primary" disabled={!available||busy} onClick={()=>{void create();}}>{busy?"Creating your QR…":`Pay ${price(packages.find(p=>p.id===selected)?.amount??0)}`}</button></>}
    {topup&&<div className="payment-receipt"><h3>{price(topup.amount)} · {topup.credits} credits</h3>
     {topup.status==="pending"&&remaining>0&&!hidden&&<><img className="payment-qr" src={topup.qr_image_url??""} alt="Payment QR Ph code"/><p>Scan with GCash or a QR Ph wallet</p><time>{String(Math.floor(remaining/60)).padStart(2,"0")}:{String(remaining%60).padStart(2,"0")}</time></>}
     <p role="status">{topup.status==="paid"?`Payment received · ${topup.credits} credits added`:topup.status==="pending"?(remaining>0?"Waiting for payment":"QR time elapsed · checking payment status"):topup.status==="creation_failed"?"QR creation unverified · check history before starting again":topup.status==="creating"?"Creating your QR…":`Payment ${topup.status}`}</p>
     {topup.status==="pending"&&<button className="button-secondary" onClick={()=>setHidden(!hidden)}>{hidden?"Show QR":"Hide QR"}</button>}
     {hidden&&<p>This hides the QR on this device. It does not cancel the payment.</p>}
     {["paid","failed","expired"].includes(topup.status)&&<button className="button-secondary" disabled={busy} onClick={newPurchase}>Start another top-up</button>}
     <p className="payment-order">Receipt: {topup.id}</p>{topup.refund_status&&<p>Refund {topup.refund_status === "succeeded" ? "processed by provider" : topup.refund_status === "held" ? "under review · credits held" : topup.refund_status}</p>}<p>{refundReviewLabel(topup.refund_eligibility)}</p></div>}
   </section>
   <section><h2>Your purchases</h2>{account.live_orders?.length?account.live_orders.map(order=><p key={order.id}><button className="button-secondary" disabled={busy} onClick={()=>{const version=++epoch.current;sessionStorage.setItem(savedKey,JSON.stringify({owner:account.user!.id,receipt:order.id}));setTopup(null);void fetchResponse(order.id).then(accountResponse).then(body=>{if(epoch.current===version)setTopup(receipt(body.topup,order.id));}).catch(()=>{if(epoch.current===version)setError("Could not open the receipt.");});}}>{order.id}</button> · {price(order.amount)} · {order.credits} credits · {order.status}{order.refund_status?` · refund ${order.refund_status}`:""}</p>):<p>No purchases yet.</p>}</section>
  </>}
  {support&&<a href={`mailto:${encodeURIComponent(support)}?subject=${encodeURIComponent(`Payment support${topup?` · ${topup.id}`:""}`)}`}>Payment support</a>}
  {(error||accountError)&&<p role="alert" className="payment-error">{error||accountError}</p>}
 </div></main>;
}
async function fetchResponse(id:string){return fetch(`/api/payments/live/topups/${encodeURIComponent(id)}`,{cache:"no-store"});}
