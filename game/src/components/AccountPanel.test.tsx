import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AccountPanel } from "./AccountPanel";
import type { Account } from "../hooks/useAccount";
const account: Account = { authenticated: true, google_enabled: true, user: {id:"private-id",name:"Alex",email:"alex@example.test"}, csrf_token:"csrf",test_credits:90,reserved_credits:10,voucher_enabled:true,free_access:false,orders:[] };
afterEach(()=>vi.unstubAllGlobals());
describe("Account access",()=>{
 it("shows live credits separately and retains voucher access without a top-up invitation",()=>{
  render(<AccountPanel account={{authenticated:true,google_enabled:true,payment_mode:"live",user:{id:"live-owner",name:"Owner",email:"owner@example.test"},live_credits:50,live_reserved_credits:10,topup_invited:false,voucher_enabled:true}} refresh={vi.fn()} error=""/>);
  expect(screen.getByText(/50 available credits/)).toBeTruthy();
  expect(screen.getByText(/Top-ups are temporarily unavailable/)).toBeTruthy();
  expect(screen.getByLabelText("Free-access voucher")).toBeTruthy();
  expect(screen.queryByRole("link",{name:"Top up credits"})).toBeNull();
 });
 it("explains unconfigured login and guest access",()=>{
  render(<AccountPanel account={{authenticated:false,google_enabled:false}} refresh={vi.fn()} error=""/>);
  expect(screen.getByText(/Google sign-in needs server configuration/)).toBeTruthy();
  expect(screen.queryByRole("link",{name:"Sign in with Google"})).toBeNull();
  expect(screen.getByText(/Teammates can join/)).toBeTruthy();
 });
 it("returns sign-in to the account drawer",()=>{
  render(<AccountPanel account={{authenticated:false,google_enabled:true}} refresh={vi.fn()} error=""/>);
  expect(screen.getByRole("link",{name:"Sign in with Google"}).getAttribute("href")).toBe("/api/auth/google/login?return_to=%2F%3Faccount%3D1");
 });
 it("shows available credits separately from reservations and private purchases",()=>{
  render(<AccountPanel account={{...account,orders:[{id:"own-order",status:"paid",credits:100,amount:10000,currency:"PHP"}]}} refresh={vi.fn()} error=""/>);
  expect(screen.getByText(/available test credits/).textContent).toContain("90");
  expect(screen.getByText(/available test credits/).textContent).toContain("10");
  expect(screen.getByText("own-order")).toBeTruthy();
  expect(screen.queryByText("private-id")).toBeNull();
 });
 it("redeems once while pending, supplies CSRF and clears the secret field",async()=>{
  let release!:()=>void;const pending=new Promise<void>(r=>release=r);
  const fetcher=vi.fn(async()=>{await pending;return {ok:true,json:async()=>({free_access:true})}});vi.stubGlobal("fetch",fetcher);
  const refresh=vi.fn(async()=>{});render(<AccountPanel account={account} refresh={refresh} error=""/>);
  const input=screen.getByLabelText("Free-access voucher") as HTMLInputElement;
  fireEvent.change(input,{target:{value:"fixture-voucher"}});
  const form=input.closest("form")!;fireEvent.submit(form);fireEvent.submit(form);
  expect(fetcher).toHaveBeenCalledTimes(1);expect((screen.getByRole("button",{name:"Redeem voucher"}) as HTMLButtonElement).disabled).toBe(true);
  expect(fetcher).toHaveBeenCalledWith("/api/auth/voucher",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":"csrf"},body:JSON.stringify({voucher:"fixture-voucher"})});
  release();await screen.findByText("Free access is active for your account.");expect(input.value).toBe("");expect(refresh).toHaveBeenCalledTimes(1);
  expect(JSON.stringify(localStorage)).not.toContain("fixture-voucher");
 });
 it("shows safe redemption failure and permits retry",async()=>{
  vi.stubGlobal("fetch",vi.fn(async()=>({ok:false,json:async()=>({detail:"Too many voucher attempts. Wait five minutes before trying again."})})));
  render(<AccountPanel account={account} refresh={vi.fn()} error=""/>);
  const input=screen.getByLabelText("Free-access voucher") as HTMLInputElement;fireEvent.change(input,{target:{value:"bad"}});fireEvent.submit(input.closest("form")!);
  await screen.findByText(/Too many voucher attempts/);expect(input.value).toBe("");await waitFor(()=>expect((screen.getByRole("button",{name:"Redeem voucher"}) as HTMLButtonElement).disabled).toBe(false));
 });
 it("explains free access and removes the redeemed voucher field",()=>{
  render(<AccountPanel account={{...account,free_access:true}} refresh={vi.fn()} error=""/>);
  expect(screen.getByText("Free access active")).toBeTruthy();expect(screen.queryByLabelText("Free-access voucher")).toBeNull();
 });
 it("shows credits actually awarded and distinguishes charges from released reservations",()=>{
  render(<AccountPanel account={{...account,spent_credits:10,orders:[{id:"pending-order",status:"pending",credits:100,awarded_credits:0}],runs:[
   {id:"run-reserved",mode:"credits",status:"reserved",cost:10,created_at:1,charged_at:null},
   {id:"run-charged",mode:"credits",status:"charged",cost:10,created_at:1,charged_at:2},
   {id:"run-released",mode:"credits",status:"released",cost:10,created_at:1,charged_at:null},
   {id:"run-free",mode:"voucher",status:"charged",cost:0,created_at:1,charged_at:null},
  ]}} refresh={vi.fn()} error=""/>);
  expect(screen.getByText("Awaiting payment verification · 0 test credits added")).toBeTruthy();
  expect(screen.getByText("Reserved · 10 test credits")).toBeTruthy();
  expect(screen.getByText("Charged · 10 test credits")).toBeTruthy();
  expect(screen.getByText("Reservation released · no credits charged")).toBeTruthy();
  expect(screen.getByText("Voucher run · no credits used")).toBeTruthy();
 });
});
