import { readFile, writeFile } from "node:fs/promises";

import protobuf from "protobufjs";

const contract = await readFile(
  new URL("../../proto/competitor_events.proto", import.meta.url),
  "utf8",
);
const root = protobuf.parse(contract, { keepCase: false }).root;
const output = new URL(
  "../src/proto/competitor-events.schema.json",
  import.meta.url,
);
await writeFile(output, `${JSON.stringify(root.toJSON(), null, 2)}\n`, "utf8");
console.log(`Generated ${output.pathname}`);
