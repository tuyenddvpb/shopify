# TASK: Meta Ad Library research for Store A "Hand Comfort"

Read `CLAUDE.md` first. Work through parts 1 to 4 in order. Write into `RESULTS-<YYYY-MM-DD>.md` (structure from `RESULTS_TEMPLATE.md`) after each item.

## Part 0: Check before starting (2 minutes)
1. Run `git pull` on branch `claude/loving-lovelace-i3iwji`.
2. Open https://www.facebook.com/ads/library/ and confirm results load and that you are logged in.
   - If you are not logged in, stop and ask the user to log in themselves.
3. Copy `RESULTS_TEMPLATE.md` to `RESULTS-<today>.md`.

## Part 1: Keyword scan (8 keywords)
Filters for every search: **Country = United States**, **Active ads**, **All ads**, **All media**.

| # | Keyword | Why |
|---|---|---|
| 1 | `heated gloves` | Core product, main market |
| 2 | `heated glove liners` | Thin liner, the exact product |
| 3 | `raynaud's` | Main angle (cold hands) |
| 4 | `cold hands` | Broader version of the angle |
| 5 | `arthritis gloves` | Compression gloves |
| 6 | `carpal tunnel` | Wrist brace and wrist wrap |
| 7 | `red light therapy hand` | VitalRay and red light gloves |
| 8 | `ergonomic crochet hook` | Gift product for makers |

For each keyword:
1. Scroll the results at most about 5 times.
2. Write down **how many ads appear** (Ad Library shows a "~N results" count) and **which advertisers appear most**.
3. Pick the **top 5 ads** in this order of priority:
   - (a) start date 14 or more days ago
   - (b) has "N ads use this creative and text" with N > 1
   - (c) sells a physical product to consumers (skip B2B, clinics, news)
4. For each of the 5 ads, open "See ad details" and record:
   - advertiser
   - start date and days running
   - number of versions
   - format (video, image, carousel, UGC or studio)
   - **hook** (the first line of the text, plus what happens in the first 3 seconds if it is a video)
   - primary text (short)
   - headline
   - CTA button
   - offer (discount, bundle, free shipping, guarantee)
   - landing page URL
5. Save 1–2 screenshots of the strongest ads.

## Part 2: Competitor advertisers (8 brands)
Search each brand name, open its page's full ad list, and record:
- total number of active ads
- the oldest active ad (start date)
- the main angles they repeat
- the products they push most
- the offers they use
- the landing page types: product page, listicle or advertorial, quiz, or collection

Brands:
1. Savior Heat
2. ActionHeat
3. Comfytemp
4. Omnilux
5. Capillus (Curavi Glove)
6. Dr. Arthritis
7. Copper Compression
8. Furls Crochet

Also add any **small or unknown store** that showed up 2 or more times in Part 1. These are often dropshippers testing the same niche, so they are the most important to note.

## Part 3: Landing page teardown (top 10)
From Parts 1 and 2, choose the **10 ads that have run longest or have the most versions**. Open each landing page (read-only) and record:
1. Page type: product page, advertorial or listicle, quiz, or homepage.
2. The section order from top to bottom, with the hero headline quoted.
3. Price, compare-at price, quantity or bundle offer tiers, guarantee, free shipping threshold.
4. Trust elements: review count and app, "as seen in", certifications, "doctor recommended".
5. Claim language about pain, arthritis, Raynaud's or FDA, quoted exactly, plus any disclaimer.
6. One screenshot of the hero and one of the offer or bundle box.

## Part 4: Synthesis (in Vietnamese, at the end of the results file)
1. **Mức độ cạnh tranh** by keyword: low, medium or high, judged by ad count and number of serious advertisers.
2. **Top 5 hooks** that appear most in long-running ads, quoted in English with a Vietnamese gloss.
3. **Top angles**:
   - pain or relief
   - Raynaud's or cold hands
   - gift or holiday
   - science or FDA
   - comparison ("unlike bulky ski gloves…")
   - UGC testimonial
   - maker or crochet
4. **Common offers** and price points.
5. **Gaps**: angles or audiences nobody is targeting, for example women 40+ with Raynaud's, "day + night" routines, or makers with sore hands.
6. **5 suggested ad concepts for Store A**: hook, format and landing page type for each.

When done:
1. Commit `ads-library-check/RESULTS-*.md` and `ads-library-check/screenshots/*`.
2. Push to `claude/loving-lovelace-i3iwji`.
3. Tell the user in Vietnamese that it is finished, with a 5-line summary.
