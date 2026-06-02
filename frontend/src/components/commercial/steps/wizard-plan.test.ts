import { describe, it, expect } from "vitest";
import { planForMode } from "./wizard-plan";

describe("planForMode", () => {
  it("quick mode runs only mode + team (2 steps)", () => {
    expect(planForMode(true)).toEqual([0, 1]);
  });

  it("full mode runs all five steps", () => {
    expect(planForMode(false)).toEqual([0, 1, 2, 3, 4]);
  });

  it("the final step differs by depth", () => {
    expect(planForMode(true).at(-1)).toBe(1);
    expect(planForMode(false).at(-1)).toBe(4);
  });
});
