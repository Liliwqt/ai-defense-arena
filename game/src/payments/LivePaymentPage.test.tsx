import {afterEach,expect,it,vi} from "vitest";
import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {LivePaymentPage} from "./LivePaymentPage";
const account={authenticated:true,google_enabled:true,user:{id:"owner",name:"Owner",email:"owner@example.test"},csrf_token:"csrf",payment_mode:"live",topup_invited:true,live_credits:0};
const packages=[{id:"credits-10",amount:100,credits:10,currency:"PHP"},{id:"credits-50",amount:500,credits:50,currency:"PHP"},{id:"credits-100",amount:1000,credits:100,currency:"PHP"}];
const topup={id:"live_fixture",mode:"live",amount:100,credits:10,currency:"PHP",status:"pending",simulated:false,qr_image_url:"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",expires_at:Math.floor(Date.now()/1000)+1800};
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();sessionStorage.clear();});
it("creates only the selected server package and shows a real QR without simulation guides",async()=>{
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages,support_email:"support@example.test"}:{topup}}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 const pay=await screen.findByRole("button",{name:"Pay ₱1.00"});fireEvent.click(pay);
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
 expect(screen.getByLabelText("Credit package")).toBeDisabled();
 expect(screen.getByText(/original package/)).toBeTruthy();
 fireEvent.click(screen.getByRole("button",{name:"Pay ₱1.00"}));
 await waitFor(()=>expect(fetcher.mock.calls.filter(([url])=>url==="/api/payments/live/topups")).toHaveLength(2));
 const calls=(fetcher.mock.calls as unknown as [string,RequestInit][]).filter(([url])=>url==="/api/payments/live/topups");
 expect(calls[0][1].body).toBe(calls[1][1].body);
 expect(calls[0][1].headers).toEqual(calls[1][1].headers);
});

it("shows the owned receipt's refund-review state without implying an automatic money refund",async()=>{
 sessionStorage.setItem("arena-live-attempt",JSON.stringify({owner:"owner",receipt:topup.id}));
 const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==="/api/auth/me"?account:url.endsWith("/config")?{mode:"live",enabled:true,packages,support_email:"support@example.test"}:{topup:{...topup,status:"paid",refund_eligibility:"unused_review"}}}));
 vi.stubGlobal("fetch",fetcher);render(<LivePaymentPage/>);
 expect(await screen.findByText("Unused purchase · contact support for refund review")).toBeTruthy();
 expect(screen.queryByRole("button",{name:/refund/i})).toBeNull();
});
