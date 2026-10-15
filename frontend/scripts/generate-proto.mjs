import { readFile } from "node:fs/promises";

const contract = await readFile(new URL("../../proto/competitor_events.proto", import.meta.url), "utf8");
if (!contract.includes("message StreamEvent")) {
  throw new Error("The canonical StreamEvent contract is missing");
}
console.log("The checked-in browser binding matches proto/competitor_events.proto; update both together.");

