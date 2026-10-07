import { describe, expect, it } from "vitest";
import { edmontonHour, plan } from "../src/dispatch";

const at = (iso: string) => Date.parse(iso);

describe("dispatch plan", () => {
  it("runs everything at minute 1 (00:01 UTC catches the daily close)", () => {
    expect(plan(at("2026-10-08T00:01:00Z"))).toEqual([{ workflow: "scan.yml", inputs: { stage: "all" } }]);
  });
  it("Stage B + exits + listings at minutes 16/31/46, listings otherwise", () => {
    expect(plan(at("2026-10-08T05:16:00Z"))[0].inputs).toEqual({ stage: "b,l" });
    expect(plan(at("2026-10-08T05:31:00Z"))[0].inputs).toEqual({ stage: "b,l" });
    expect(plan(at("2026-10-08T05:46:00Z"))[0].inputs).toEqual({ stage: "b,l" });
    for (const m of ["06", "11", "21", "26", "36", "41", "51", "56"])
      expect(plan(at(`2026-10-08T05:${m}:00Z`))[0].inputs).toEqual({ stage: "l" });
  });
  it("daily digest at 07:00 Edmonton: 13:01 UTC in summer (MDT), 14:01 UTC in winter (MST)", () => {
    expect(edmontonHour(at("2026-10-08T13:01:00Z"))).toBe(7);
    expect(plan(at("2026-10-08T13:01:00Z")).map(d => d.workflow)).toEqual(["scan.yml", "daily.yml"]);
    expect(plan(at("2026-10-08T14:01:00Z")).map(d => d.workflow)).toEqual(["scan.yml"]);
    expect(plan(at("2026-12-08T14:01:00Z")).map(d => d.workflow)).toEqual(["scan.yml", "daily.yml"]);
    expect(plan(at("2026-12-08T13:01:00Z")).map(d => d.workflow)).toEqual(["scan.yml"]);
    expect(plan(at("2026-10-08T13:06:00Z")).map(d => d.workflow)).toEqual(["scan.yml"]);
  });
});
