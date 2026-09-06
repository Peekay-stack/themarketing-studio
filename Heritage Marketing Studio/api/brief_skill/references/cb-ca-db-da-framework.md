# CB / CA → DB / DA Framework

The Current Behaviour / Current Attitude → Desired Behaviour / Desired Attitude framework isolates what communication has to *shift*, not just what it has to say. It is the planning bridge between the NeedScope read and the SMP.

## The four cells

| Cell | What it captures | Sources |
|---|---|---|
| CB — Current Behaviour | Observable purchase and usage patterns today. Where, when, how much, with whom, for what occasion | HH consumption data, retail audits, qualitative interviews, social listening |
| CA — Current Attitude | How the brand is held in the consumer's head today — affection, indifference, trust, fatigue, status. Includes one verbatim consumer quote | Qualitative research, brand tracker, reviews, social sentiment |
| DB — Desired Behaviour | The new behaviours the brand wants over the next 12–24 months — new occasions, new baskets, trade-up, share of voice, advocacy | Strategy team, ambition statement, business plan |
| DA — Desired Attitude | The new way of holding the brand — what shifts in the way consumers think and feel about it. Includes the aspirational quote | Strategic narrative, planning workshops |

## Populating the cells

### CB — Current Behaviour

Three bullets, each one observable and quantifiable. Use HH consumption data if uploaded. Examples of the form to follow:

- "Reflex purchase at ₹5 — habit, not choice."
- "Consumed only at chai-time and in kid lunchboxes; rarely the hero of any occasion."
- "Materially under-represented in quick-commerce baskets and Gen-Z snacking repertoires."

### CA — Current Attitude

A verbatim quote in inverted commas — three lines, pulled from qualitative research where available, otherwise written in plain consumer voice based on category memory. Then two short declarative lines naming the underlying emotional state.

Example:

> "The cheap, dependable biscuit my family always had — basic, trusted, slightly dated."
>
> Affection is passive.
> A memory, not a choice.

### DB — Desired Behaviour

Three bullets, each one specific enough to know whether it has happened. Examples:

- "Actively chosen across new occasions: study, post-workout, tiffin upgrade, festival gifting."
- "Trade-up within franchise: classic → fortified variant → family pack."
- "Earned cultural share of voice on social, especially around results day and comfort-food moments."

### DA — Desired Attitude

The aspirational quote in inverted commas — three lines, in the voice the consumer would use if the strategic shift succeeded. Then two short declarative lines naming the new emotional state.

Example:

> "Parle-G is the biscuit India grows on — affordable ambition that respects everyone."
>
> Active pride, not affection.
> "Still ₹5, still mine, still the spark."

## The shift line

The most important sentence in the entire framework. One line, present-tense verb, ending in a full stop.

Formula: `From {current emotional state} to {desired emotional state}.`

Examples:
- "From passive trust to active pride."
- "From dependable utility to quietly aspirational craft."
- "From mass familiarity to chosen everyday luxury."

Underneath the diagram, always write a one-sentence caption naming the implication: the desired attitude is *layered on top of* the current one, not a replacement. The NeedScope anchor stays; a single thread is added.

## Generating the diagram

Use `assets/cbca_dbda_template.svg`. It contains the two-card chrome (left grey "CURRENT", right green "DESIRED"), the four labelled sub-cards, the green arrow, and the caption slot. The skill:

1. Reads the template.
2. Substitutes placeholder strings for the CB bullets, CA quote, CA declarative lines, DB bullets, DA quote, DA declarative lines, the shift line, and the caption.
3. Writes the result to `outputs/cbca_dbda_filled.svg`.
4. Converts to PNG with `cairosvg` at 1800 px width.

## Placeholder tokens in the template

The template uses these tokens, which the skill replaces with actual content:

| Token | What to substitute |
|---|---|
| `{{CB_LINE_1}}` ... `{{CB_LINE_6}}` | Six visual lines covering the three CB bullets (each bullet wraps to two text lines) |
| `{{CA_QUOTE_1}}` ... `{{CA_QUOTE_3}}` | Three lines of the current-attitude verbatim quote |
| `{{CA_DECLARATIVE_1}}` ... `{{CA_DECLARATIVE_2}}` | Two declarative summary lines |
| `{{DB_LINE_1}}` ... `{{DB_LINE_6}}` | Six visual lines for the three DB bullets |
| `{{DA_QUOTE_1}}` ... `{{DA_QUOTE_3}}` | Three lines of the desired-attitude aspirational quote |
| `{{DA_DECLARATIVE_1}}` ... `{{DA_DECLARATIVE_2}}` | Two declarative summary lines |
| `{{SHIFT_FROM}}` | The "current state" half of the shift line |
| `{{SHIFT_TO}}` | The "desired state" half of the shift line |
| `{{CAPTION}}` | The sentence beneath the diagram |

Keep each line under 36 characters so the text does not overflow the card width.

## Common pitfalls

- Writing DB as if it is a campaign objective ("increase awareness by 10 points"). DB is behaviour, not a metric. Reframe metrics as the behaviour they reflect.
- Writing DA in the brand's own voice rather than the consumer's voice. Use first person and inverted commas.
- Putting a totally new attitude in DA that is unrelated to CA. The shift has to be reachable from the current state — there must be a credible bridge.
- Asking the communication to do all the work. The DB shift almost always also needs a product or pricing move; flag that in the brief's recommended actions, not in this diagram.
