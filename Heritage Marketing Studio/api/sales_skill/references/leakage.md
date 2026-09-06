# How trade money leaks, and what catches it

Every trade incentive has a failure mode. This is not cynicism about the trade — it is arithmetic. If
a scheme pays for a behaviour, and the behaviour is cheaper to *report* than to *perform*, some share
of the money buys the report.

The rule the skill enforces: **name this scheme's leakage and its control.** "We will monitor it" is
not a control.

## The common patterns

**Loading.** The retailer or distributor takes the scheme quantity without any change in offtake.
Stock sits, reorders stop, and the next quarter looks terrible for reasons nobody connects to this
quarter's scheme.
*Catches it:* measure secondary or tertiary offtake, not primary dispatch. Cap scheme quantity against
the outlet's historical rate of sale rather than against appetite.

**Diversion across territories.** Scheme goods bought cheaply in one market reappear in another below
the local distributor's price. Usually flows through wholesale.
*Catches it:* territory coding on cartons, scheme caps per outlet, and watching for a distributor whose
purchases outrun their addressable outlets.

**Phantom outlets and phantom orders.** Orders booked against outlets that do not exist, or exist and
did not order. The salesman's incentive is paid on booking.
*Catches it:* geo-fenced order capture — the order can only be booked at the outlet's location — plus
OTP confirmation from the retailer, and periodic physical audit of new outlet additions.

**Unperformed display.** The display incentive is claimed and the display was never built, or came
down the day after the photograph.
*Catches it:* timestamped, geotagged photographs at two points in the period rather than one, and
paying part of the incentive at the end rather than all of it up front.

**Claim inflation.** Invoices or volumes overstated in the claim, or the same invoice claimed twice.
*Catches it:* invoice upload with multi-level approval, and duplicate detection on invoice number.

**Loyalty points farming.** Points earned on purchases that are returned, cancelled, or made by a
related party; or a single retailer operating several enrolments.
*Catches it:* QR or unique-code scanning tied to the physical unit, earn reversal on return, and
one enrolment per verified GST or outlet identity.

**Promoter idle time.** In-store promoters paid for hours rather than outcomes, at outlets with too
little footfall to justify them.
*Catches it:* promoter productivity per outlet as a reported number, and a floor below which the
outlet loses the promoter.

## The controls, plainly

The practitioner toolkit is well established: **geo-fencing** for field staff, **OTP confirmation**
from the retailer, **QR or unique-code scanning** on the unit, **invoice upload with multi-level
approval**, and **automated allocation per SKU** rather than manual credit. Use the ones that fit the
scheme; do not list all six to look thorough.

## Two rules worth stating in the plan itself

**Never let the person paid on the result be the only person who reports it.** This is the single most
reliable predictor of a gamed scheme. If the salesman's incentive depends on the number the salesman
submits, the number will improve.

**Pay in arrears, at least in part.** An incentive fully paid on promise rather than performance has
no recourse. Splitting it — some on compliance, the balance on measured offtake — costs nothing and
changes behaviour.

## What to write in the plan

For each scheme, one line each:

- **Leakage mode** — the specific way this one gets gamed, not a generic list.
- **Control** — the mechanism, named.
- **Residual risk** — what the control does *not* catch. Every control has a gap, and writing it down
  is what stops someone treating the control as a guarantee.
