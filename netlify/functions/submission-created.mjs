import { getStore, connectLambda } from "@netlify/blobs";

// Runs automatically on every Netlify Forms submission. Stores only the time,
// which form it came from, and whether it was a QA test submission (so test
// traffic never inflates the real lead count on the dashboard).
export const handler = async (event) => {
  connectLambda(event);
  const { payload } = JSON.parse(event.body);
  // Only website enquiries count as leads; client questionnaires do not.
  if (payload?.form_name && payload.form_name !== "contact") return { statusCode: 200 };
  const ts = Date.now();
  const source = String(payload?.data?.source || "unknown").slice(0, 40);
  const test = payload?.data?.test === "true" || payload?.data?.test === true;
  await getStore("submissions").setJSON(
    `${new Date(ts).toISOString().slice(0, 10)}/${ts}-${Math.random().toString(36).slice(2, 8)}`,
    { ts, source, test }
  );
  return { statusCode: 200 };
};
