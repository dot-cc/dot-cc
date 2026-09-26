import { getStore, connectLambda } from "@netlify/blobs";

// Runs automatically on every Netlify Forms submission. Stores only the time and which form it came from.
export const handler = async (event) => {
  connectLambda(event);
  const { payload } = JSON.parse(event.body);
  const ts = Date.now();
  const source = String(payload?.data?.source || "unknown").slice(0, 40);
  await getStore("submissions").setJSON(
    `${new Date(ts).toISOString().slice(0, 10)}/${ts}-${Math.random().toString(36).slice(2, 8)}`,
    { ts, source }
  );
  return { statusCode: 200 };
};
