import {afterEach,beforeEach,expect,it,vi} from "vitest";
import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {LivePaymentPage} from "./LivePaymentPage";
const account={authenticated:true,google_enabled:true,user:{id:"owner",name:"Owner",email:"owner@example.test"},csrf_token:"csrf",payment_mode:"live",topup_invited:true,live_credits:0};
const packages=[{id:"credits-10",amount:100,credits:10,currency:"PHP"},{id:"credits-50",amount:500,credits:50,currency:"PHP"},{id:"credits-100",amount:1000,credits:100,currency:"PHP"}];
const topup={id:"live_fixture",mode:"live",amount:100,credits:10,currency:"PHP",status:"pending",simulated:false,qr_image_url:"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",expires_at:Math.floor(Date.now()/1000)+1800};
beforeEach(()=>{sessionStorage.clear();});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();sessionStorage.clear();});
it("creates only the selected server package and shows a real QR without simulation guides",async()=>{
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages,support_email:"support@example.test"}:{topup}}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 const pay=await screen.findByRole("button",{name:"Pay ₱1.00"});await waitFor(()=>expect(pay).not.toBeDisabled());fireEvent.click(pay);
 expect(await screen.findByRole("img",{name:"Payment QR Ph code"})).toBeTruthy();
 await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>url==="/api/payments/live/topups")).toBe(true));
 expect(screen.queryByText(/simulat|configure|test credits/i)).toBeNull();
 expect(screen.getByRole("link",{name:"Payment support"}).getAttribute("href")).toContain("live_fixture");
});

it("restores a historical receipt without using today's catalog or creating another purchase",async()=>{
 const historic={...topup,amount:200,credits:75};
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:historic.id}));
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages,support_email:"support@example.test"}:{topup:historic}}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 expect(await screen.findByRole("heading",{name:"₱2.00 · 75 credits"})).toBeTruthy();
 expect(fetcher.mock.calls.some(([url])=>url==="/api/payments/live/topups")).toBe(false);
});

it("keeps an ambiguous attempt's key and freezes its package when retrying",async()=>{
 const fetcher=vi.fn(async(url:string)=>{
  if(url==="/api/payments/live/topups")return {ok:false,json:async()=>({detail:"The QR could not be verified. Your attempt is retained."})};
  return {ok:true,json:async()=>url==="/api/auth/me"?account:{mode:"live",enabled:true,packages,support_email:"support@example.test"}};
 });
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 fireEvent.click(await screen.findByRole("button",{name:"Pay ₱1.00"}));
 await screen.findByRole("alert");
 expect(screen.getByRole("radio",{name:"₱1.00 10 credits"})).toBeDisabled();
 expect(screen.getByText(/original package/)).toBeTruthy();
 fireEvent.click(screen.getByRole("button",{name:"Retry purchase"}));
 await waitFor(()=>expect(fetcher.mock.calls.filter(([url])=>url==="/api/payments/live/topups")).toHaveLength(2));
 const calls=(fetcher.mock.calls as unknown as [string,RequestInit][]).filter(([url])=>url==="/api/payments/live/topups");
 expect(calls[0][1].body).toBe(calls[1][1].body);
 expect(calls[0][1].headers).toEqual(calls[1][1].headers);
});

it("downloads the exact server-issued PNG with a safe receipt filename",async()=>{
 const issued={...topup,id:"live/receipt:123"};
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:issued.id}));
 vi.stubGlobal("fetch",vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages}:{topup:issued}})));
 render(<LivePaymentPage/>);
 const download=await screen.findByRole("link",{name:/Download QR code/});
 expect(download).toHaveAttribute("href",issued.qr_image_url);
 expect(download).toHaveAttribute("download","payment-qr-live_receipt_123.png");
 fireEvent.click(screen.getByRole("button",{name:"Hide QR"}));
 expect(screen.queryByRole("link",{name:/Download QR code/})).toBeNull();
 fireEvent.click(screen.getByRole("button",{name:"Show QR"}));
 expect(screen.getByRole("link",{name:/Download QR code/})).toHaveAttribute("href",issued.qr_image_url);
});

it.each([
 {status:"paid",expires_at:topup.expires_at},
 {status:"failed",expires_at:topup.expires_at},
 {status:"expired",expires_at:topup.expires_at},
 {status:"pending",expires_at:Math.floor(Date.now()/1000)-1},
])("does not offer an unusable QR for $status",async overrides=>{
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:topup.id}));
 vi.stubGlobal("fetch",vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages}:{topup:{...topup,...overrides}}})));
 render(<LivePaymentPage/>);
 await screen.findByRole("heading",{name:"₱1.00 · 10 credits"});
 expect(screen.queryByRole("link",{name:/Download QR code/})).toBeNull();
 expect(screen.queryByRole("img",{name:"Payment QR Ph code"})).toBeNull();
});

it("keeps history readable and blocks new purchase actions while opening an owned receipt",async()=>{
 const historic={...topup,id:"live_history",status:"paid",amount:500,credits:50,created_at:1760000000};
 let finish!: (value:unknown)=>void;
 const read=new Promise(resolve=>{finish=resolve;});
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?{...account,live_orders:[historic]}:url.endsWith("/config")?{mode:"live",enabled:true,packages}:await read}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 const view=await screen.findByRole("button",{name:"View receipt live_history"});
 expect(screen.getByText("Paid")).toBeTruthy();
 expect(screen.getByText("50 credits",{selector:".payment-purchase-meta span"})).toBeTruthy();
 expect(document.querySelector("time[datetime]")).toHaveAttribute("datetime",new Date(historic.created_at*1000).toISOString());
 fireEvent.click(view);fireEvent.click(view);
 expect(await screen.findByText("Opening your receipt…")).toBeTruthy();
 expect(view).toBeDisabled();
 expect(screen.queryByRole("button",{name:/Pay ₱/})).toBeNull();
 finish({topup:historic});
 await screen.findByRole("heading",{name:"₱5.00 · 50 credits"});
 expect(fetcher.mock.calls.filter(([url])=>url==="/api/payments/live/topups/live_history")).toHaveLength(1);
 expect(fetcher.mock.calls.some(([url])=>url==="/api/payments/live/topups")).toBe(false);
});

it("retains a failed history read and retries the same receipt without a new purchase",async()=>{
 let failed=true;
 const fetcher=vi.fn(async(url:string)=>{
  if(url.endsWith(`/topups/${topup.id}`))return failed?{ok:false,json:async()=>({detail:"Unavailable"})}:{ok:true,json:async()=>({topup})};
  return {ok:true,json:async()=>url==="/api/auth/me"?{...account,live_orders:[topup]}:{mode:"live",enabled:true,packages}};
 });
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 fireEvent.click(await screen.findByRole("button",{name:`View receipt ${topup.id}`}));
 await screen.findByRole("alert");failed=false;
 fireEvent.click(screen.getByRole("button",{name:"Retry purchase"}));
 await screen.findByRole("link",{name:/Download QR code/});
 expect(fetcher.mock.calls.some(([url])=>url==="/api/payments/live/topups")).toBe(false);
});

it("rejects invalid QR data instead of offering it for download",async()=>{
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:topup.id}));
 vi.stubGlobal("fetch",vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages}:{topup:{...topup,qr_image_url:"https://unverified.example/qr.png"}}})));
 render(<LivePaymentPage/>);
 await screen.findByRole("alert");
 expect(screen.queryByRole("link",{name:/Download QR code/})).toBeNull();
});

it("removes an existing QR download when returning after its deadline",async()=>{
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:topup.id}));
 vi.stubGlobal("fetch",vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages}:{topup}})));
 render(<LivePaymentPage/>);
 await screen.findByRole("link",{name:/Download QR code/});
 vi.spyOn(Date,"now").mockReturnValue(topup.expires_at*1000);
 fireEvent(window,new Event("focus"));
 await waitFor(()=>expect(screen.queryByRole("link",{name:/Download QR code/})).toBeNull());
 expect(screen.getByText("QR time elapsed · checking payment status")).toBeTruthy();
});

it("shows the owned receipt's refund-review state without implying an automatic money refund",async()=>{
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:topup.id}));
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages,support_email:"support@example.test"}:{topup:{...topup,status:"paid",refund_eligibility:"unused_review"}}}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 expect(await screen.findByText("Unused purchase · contact support for refund review")).toBeTruthy();
 expect(screen.queryByRole("button",{name:/refund/i})).toBeNull();
});
