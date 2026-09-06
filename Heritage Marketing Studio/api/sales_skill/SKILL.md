---
name: trade-activation
description: Build a route-to-market and trade activation plan — general trade, wholesale, modern trade, e-commerce, quick commerce, own retail and home delivery held in one view. Names the behaviour each scheme buys, its payback net of cost, how it will be gamed, and reconciles effective consumer price across channels so channel conflict surfaces before launch. Use when asked for a trade plan, trade activation, trade scheme, route to market, channel plan, distributor or retailer incentive, retailer loyalty programme, modern trade or quick commerce plan.
---

# Trade activation

Trade spend is usually the largest line in a marketing budget and the least measured. This plans it
in a way that can be argued with.

It belongs to the same sequence as the rest:

> **Brief → Messaging house → IMC plan → Executions** — and this is one of those executions

The audience here is **the trade, not the consumer**. A distributor, a kirana owner, a modern-trade
buyer and a q-commerce category manager each hear a different argument, and none of them is the
argument you make to a shopper. If the messaging house has a trade message, use it. If it does not,
say so — do not borrow the consumer line and hope.

## One plan, all channels — and that is the point

Do not plan general trade and quick commerce in separate documents. **Channel conflict is the central
risk in trade**, and it is invisible unless every channel sits in one view: the same strategy applied
across channels produces stock imbalances, inconsistent promotions and lost profitability. The single
most valuable output here is the reconciliation of effective consumer price across channels.

Channels to cover, all of them, even where a channel gets one line:

| Channel | Shorthand |
|---|---|
| General trade | kirana, the long tail — still the large majority of Indian FMCG value |
| Wholesale | traditional wholesale and cash & carry |
| Modern trade | organised chains; listing, planogram, promoters, joint business plans |
| E-commerce | Amazon, Flipkart, BigBasket — content, search, ratings, fill rate |
| Quick commerce | Blinkit, Zepto, Instamart — dark-store assortment, in-app share, platform ads |
| Own retail | brand parlours and outlets, where they exist |
| Home delivery | subscription and daily delivery, decisive in daily categories |

What each channel actually rewards, what its levers are, and how each one characteristically goes wrong: `references/channels.md`. Read it before assigning a lever — the same rupee behaves differently in each, and wholesale in particular is where a good scheme becomes someone else's cheap stock.

**For daily cold-chain categories — dairy, fresh — weight this deliberately.** General trade and home
delivery dominate, and quick commerce is *less* disruptive than in snacks and beverages, because dark
stores cannot match an established cold chain. Do not over-index a channel because it is fashionable.
Say what share of volume each channel actually holds today before assigning any money.

## The eight layers

One at a time. Offer 3–5 real options, number them, stop, and ask.

**1. Route to market.** Every channel, its **current share of volume**, and its role: *volume ·
reach · premium · trial · defence*. A channel with no role does not get money.

**2. The behaviour to buy.** The core of the whole plan, and where most trade plans fail. Not
"activate general trade" — *"move 40,000 outlets from fortnightly to weekly ordering"*, *"get two
facings in the chiller instead of one"*, *"add the 500ml pack to 12,000 outlets that stock only the
1L"*. A scheme that buys "visibility" buys nothing you can measure. Name the behaviour, the baseline
and the target.

**3. The lever.** Matched to that behaviour, from: retailer margin · trade scheme · display incentive
· loyalty programme · listing and terms of trade · promoter or ISD · credit terms · platform ad
spend · assortment and pack architecture. A lever that does not plausibly cause the behaviour in
layer 2 is decoration.

**4. Economics.** Cost per unit of behaviour bought, and payback **net of the scheme**. Effectiveness
here means a defined period and territory linked to a measurable lift in offtake, minus what the
scheme cost. If a number is unknown, write `payback unknown` — never estimate it into existence.

**5. Leakage and gaming.** Every trade incentive has a failure mode. Name this one's, and the control
that catches it. See `references/leakage.md`. A scheme without a leakage model is a donation.

**6. Channel conflict.** The **effective consumer price** in each channel after every scheme, promo
and platform discount, side by side. Then the judgement: where do they collide, and does it matter?
A quick-commerce offer that undercuts the kirana who stocks you daily has bought volume and lost
distribution.

**7. Sell-through proof.** For each scheme, state whether it moves **primary** (to the distributor),
**secondary** (to the retailer) or **tertiary** (to the consumer), and how you will know. Primary-only
schemes produce phantom growth and a returns problem six weeks later.

**8. Calendar.** Tied to the IMC plan's buying occasions, with the trade lead time in front of each —
trade has to be stocked before consumers are told.

## Discipline — enforce these on yourself

1. **Name the behaviour or drop the scheme.** "Visibility", "engagement" and "excitement" are
   rejected. If you cannot say what someone will do differently, there is nothing to buy.
2. **Every scheme carries a payback, or an explicit `payback unknown`.** Never a number you made up.
   An invented ROI is the most expensive sentence in a trade plan.
3. **Every scheme carries a leakage model and a control.** Not "we will monitor it".
4. **Name who receives the money** — retailer, wholesaler, salesman, platform, consumer. Who
   receives it determines who games it, and schemes paid to the person who reports the result are
   the ones that get gamed hardest.
5. **Reconcile effective consumer price across channels.** Every time. Flag collisions rather than
   averaging them away.
6. **State the sell-through level.** Primary-only is flagged, always.
7. **Mark sources.** `[brief]`, `[house]`, `[plan]`, or `[unverified]` for anything you supplied.
   Shares, margins, outlet counts and platform fees are exactly the numbers that get invented — if
   you do not have them, say the plan needs them.
8. **Thin data, thin plan.** If channel shares are unknown, the plan says so and stays short. A
   confident trade plan on invented shares is worse than an honest gap, because trade money moves
   fast and quietly.

## Style

Write for someone who will have to defend this to a sales director. Short declaratives, real numbers
where they exist, and the trade-off named rather than smoothed. No "synergies", no "win-win". A
scheme a TSI can explain to a retailer in one sentence beats a scheme that scans well in a deck.

## Output

**A working table each time a layer is decided** — editable and copy-pasteable.

**A channel grid on one page** — once route to market and the behaviours are decided, render it as a
self-contained editable HTML artifact. The shape is in `references/grid.md`: one row per channel
carrying role, behaviour, lever, cost per unit, leakage control and sell-through level, plus the
**effective-price reconciliation strip** — the part nobody usually draws and the part that prevents
the most expensive mistake.

At the end, offer a `.docx` or `.xlsx` version, or a JSON block.
