# Ads Library check: context for this session

You are running locally on the user's computer with browser access, through the Claude desktop app's built-in browser or the Claude in Chrome extension. Your job is to research competitor ads in **Meta Ad Library** for a new Shopify store and write the findings to files in this folder.

## The user and the project
- The user is a Vietnamese dropshipper selling to the **US market**. **Write every report in Vietnamese.** Keep ad copy quotes in their original English.
- The user already runs **VitalRay** (vitalray.shop), a store selling a red light therapy wrist wrap (660nm + 850nm) for "everyday hand & wrist comfort".
- The user is building **Store A, "Hand Comfort"**. The target customer is a woman aged 40–65 with cold, stiff or achy hands: Raynaud's, arthritis, carpal tunnel, or a knitter or crocheter with sore hands.
- Planned products:
  - Thin rechargeable heated glove liners, touchscreen-compatible ($79–99)
  - The VitalRay red light wrist wrap
  - A night wrist brace without velcro ($29–39)
  - Arthritis compression gloves ($24–29)
  - An ergonomic crochet hook gift set ($39–59)
  - A "day + night" bundle
- Competitors already studied from their websites (see `../docs/research/2026-11-doi-thu-store-a.md`): Comfytemp, Savior Heat, ActionHeat, Omnilux (Contour Glove $345), Capillus Curavi Glove ($899), Furls Crochet, plus Amazon brands such as Dr. Arthritis, IMAK and Copper Compression.
- Background niche research: `../docs/research/2026-11-tong-hop-ngach.md`.

## What you are looking for
Ads that are **profitable enough to keep running**. In practice:
- Ads that have been active for **14 days or more**. 2–5 weeks is the sweet spot; months-long ads are evergreen winners.
- Ads with **several versions** ("N ads use this creative and text"), because advertisers scale what works.
- The **hook** (first line or first 3 seconds), the **angle** (pain, gift, science, comparison, UGC testimonial), the **offer**, and the **landing page** the ad sends people to.

## Rules (must follow)
1. **Read-only.**
   - Never click "Like", comment, message, follow, or press any button that buys, subscribes or signs up.
   - On landing pages, never add to cart past the cart page and never enter personal data.
2. **Never type passwords or handle login.**
   - If Facebook asks you to log in, or shows a captcha, checkpoint or "temporarily blocked" message, **stop and ask the user to handle it in the browser**, then continue.
   - Never try to get around a block.
3. **Go slowly, like a person.**
   - Use one tab at a time and pause a few seconds between searches.
   - Scroll a results page at most about 5 times.
   - If you are rate-limited, stop for 30+ minutes and tell the user.
4. **Save as you go.**
   - Write findings to `RESULTS-<YYYY-MM-DD>.md` (copy the structure of `RESULTS_TEMPLATE.md`) after each keyword or competitor, so nothing is lost if the session stops.
   - Save useful screenshots to `screenshots/` with names like `kw-heated-glove-liners-01.png` or `adv-saviorheat-01.png`.
5. **Be accurate.**
   - Copy start dates, version counts and ad text exactly as shown.
   - If something is not visible, write "không thấy", never guess.
   - Ad Library does **not** show spend or sales for commercial ads, so do not invent them.
6. **Git.**
   - Work on branch `claude/loving-lovelace-i3iwji`. Run `git pull` before you start.
   - When finished, commit only files inside `ads-library-check/`, then push. Do not create a pull request.
   - End the commit message with the attribution lines your harness gives you (if any).

## Useful Ad Library facts
- Keyword search URL pattern:
  `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&media_type=all&search_type=keyword_unordered&q=<keyword>`
- Exact phrase: use `search_type=keyword_exact_phrase`.
- An advertiser's full ad list: click the page name on an ad, or use `view_all_page_id=<id>` in the URL.
- Each ad card shows "Started running on <date>", Library ID, the platforms it runs on, and sometimes "N ads use this creative and text". Open "See ad details" for all versions and the landing URL.
- Today's date tells you how many days an ad has run: today minus the start date.
