// People get the interactive site; crawlers and AI tools get the text pages.
//
// The text pages (/tech-studio/, /ar/creative-studio/, /case-studies/..., etc.)
// exist so search engines and AI assistants can read the site, because the
// interactive site at / keeps its content inside JavaScript. When a person
// opens one of those addresses (from Google, ChatGPT, a shared link...), this
// serves them the interactive site at the same address instead. The script at
// the top of public/index.html then opens the matching studio in the page's
// language.
//
// Google calls this "dynamic rendering" and accepts it as long as both
// versions carry the same content. They do: the text pages are built from the
// interactive site's own copy.
//
// Anyone can still see a text page by adding ?text=1 to its address.
//
// /ar/creative-studio/ is left out on purpose: the interactive creative studio
// is English-only, so Arabic readers keep the Arabic text page (which links to
// the interactive site). Add it back once that studio has an Arabic version.

// Crawlers, link-preview fetchers and AI tools, matched by user agent.
// Keep in-app browsers (LinkedIn, Facebook, Instagram, X) on the people side:
// only their preview bots are listed, never the app names on their own.
const BOT = new RegExp([
  "bot\\b", "bot/", "crawl", "spider", "slurp", "preview", "fetcher",
  "googlebot", "googleother", "google-", "-google",
  "bingbot", "msnbot", "adidxbot", "duckduck", "yandex", "baidu", "sogou", "exabot", "petalbot", "applebot",
  "gptbot", "chatgpt", "oai-searchbot", "openai", "perplexity", "claude", "anthropic", "ccbot", "cohere",
  "bytespider", "amazonbot", "meta-externalagent", "diffbot",
  "facebookexternalhit", "facebot", "linkedinbot", "twitterbot", "slackbot", "slack-imgproxy", "discordbot",
  "telegrambot", "whatsapp", "skypeuripreview", "pinterestbot", "redditbot", "embedly", "iframely", "vkshare",
  "semrush", "ahrefs", "mj12bot", "dotbot", "ia_archiver", "archive\\.org", "headless", "phantomjs",
].join("|"), "i");

export function isPerson(userAgent) {
  // Every real browser, including in-app browsers, sends a Mozilla/5.0 user agent.
  return userAgent.startsWith("Mozilla/") && !BOT.test(userAgent);
}

export default async (request, context) => {
  const url = new URL(request.url);
  const person = isPerson(request.headers.get("user-agent") || "");
  if (request.method === "GET" && person && url.searchParams.get("text") !== "1") {
    // Serve the interactive site's page at this address (a rewrite, not a redirect).
    return new URL("/", request.url);
  }
  // Crawlers, AI tools and ?text=1 get the text page. Vary tells caches (and
  // Google) that this address answers differently depending on the user agent.
  const response = await context.next();
  response.headers.set("vary", "User-Agent");
  return response;
};

export const config = {
  path: [
    "/tech-studio/", "/tech-studio-results/", "/tech-studio-profile/",
    "/creative-studio/", "/creative-consultancy/", "/contact/", "/case-studies/*",
    "/ar/", "/ar/tech-studio/", "/ar/tech-studio-results/", "/ar/tech-studio-profile/",
    "/ar/creative-consultancy/", "/ar/contact/", "/ar/case-studies/*",
  ],
};
