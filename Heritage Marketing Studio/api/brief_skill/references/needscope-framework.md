# NeedScope Framework

NeedScope (Kantar) is an emotional brand positioning framework. Six emotional needs are arranged on a colour-coded wheel. Each brand's communications point to one or two of them.

## The six territories

| Colour | Territory | Need shorthand | Communication cues that anchor here |
|---|---|---|---|
| Red | Power | Strength, performance, dominance | Active verbs, performance language, masculine-coded energy, hero films, competitive metaphors |
| Orange | Freedom | Self-expression, spontaneity, anti-establishment | Individualism, "break free" language, irreverent or playful tone, youthful counter-culture coding |
| Yellow | Vitality | Optimism, fun, sociable warmth | Smile equity, bright palettes, sharing and togetherness, social-occasion cues |
| Green | Belonging | Family, intimacy, inclusive warmth | Heritage, every-home ubiquity, intergenerational stories, comfort metaphors, classless framing |
| Blue | Security | Trust, control, reliability | Process language, "proven", ritual language, calm authority, expert testimonials |
| Purple | Discernment | Sophistication, refinement, status | Sensorial language, cinematic visuals, restraint, premium materials, romance and indulgence coding |

The wheel rotation is fixed clockwise from twelve o'clock: Power, Freedom, Vitality, Belonging, Security, Discernment. Never reorder the wheel — consistency across briefs makes them comparable.

## How to assign a brand to a territory

For each brand, gather:

- Current tagline.
- Two or three recent campaign films or hero ads (or descriptions if no video).
- Packaging cues (colour, typography, character/mascot, price point).
- Tone of voice in copy.

Then:

1. **Identify the primary need** the brand speaks to. Use the cue column above. If the brand speaks to two adjacent needs, pick the dominant one and treat the other as a "pull" direction.
2. **Locate the pin** at a radius of roughly 120–160 (in the 800×640 viewBox of the template) from the wheel centre `(400, 320)`. Pins closer to the centre indicate a brand that straddles territories; pins further out indicate strong commitment to a single territory.
3. **Mark the anchor brand** (the focal brand of this brief) with a slightly larger pin (radius 11) and the label "(anchor)" below it.

## Reading user-uploaded NeedScope charts

If the user uploaded a NeedScope chart (image, PDF, or PPTX slide):

- Read the image with vision tools.
- Identify which brands sit in which territories and roughly where.
- Reproduce those positions in the wheel rather than inferring fresh ones from communications.
- If a brand on the user's chart is not in scope for this brief, drop it. If a brand in scope is missing, add it via the communications method.

## The strategic-bridge arrow

Once all brands are placed, the wheel must include a dashed arrow from the anchor brand to the adjacent territory the brand should *extend into*. This is the brand's strategic move — and it must match the SMP narrative.

Pick the bridge territory using these rules:

- The bridge territory must be adjacent on the wheel (one step clockwise or anti-clockwise from the anchor's territory).
- It must be a territory not strongly owned by a direct competitor, or where the anchor brand has unique permission a competitor cannot match.
- It must be reachable from the anchor's existing equity without breaking it — usually by introducing a single new dimension (e.g. ambition, performance, indulgence) while keeping the original anchor intact.

Label the arrow with the platform name in quotes (e.g. `"G for Genius"` or `"Pure Power"`) and the words "strategic bridge" beneath.

## Reading the wheel — the standard interpretation paragraph

In the brief, after the figure, always write exactly two short subsections:

### Reading the wheel

State, for each major brand on the wheel, its primary territory and any pull. Note which territories are crowded, which have a single owner, and which are empty whitespace.

### Strategic implication

Name the wheel's strategic implication for the anchor brand in one paragraph. Default formula:

> Do not chase the claimed poles — they have defined owners. Defend [anchor territory] by activating it, and extend a single disciplined thread into [bridge territory] via the "[platform name]" platform. No competitor has permission to occupy this bridge: [name three competitors and why each cannot match it].

Adapt the formula to the specifics. Never copy it verbatim.

## Generating the wheel image

Use `assets/needscope_template.svg`. It contains the wheel chrome (six coloured sectors, territory labels, centre badge) but blank space for brand pins. The skill:

1. Reads the template.
2. Injects brand pins as additional `<circle>` and `<text>` elements at the computed coordinates.
3. Injects the strategic-bridge arrow as a `<path>` and accompanying labels.
4. Writes the result to `outputs/needscope_filled.svg`.
5. Converts to PNG with `cairosvg` at 1800 px width for crisp embedding in the docx.

### Coordinate helper

```python
import math
CENTER = (400, 320)
def polar(theta_deg, r):
    t = math.radians(theta_deg)
    return (CENTER[0] + r * math.cos(t), CENTER[1] + r * math.sin(t))
```

Standard radii: 125 for anchor brand, 140 for major competitors, 150 for fringe brands.
Standard angle for each territory's centre:

| Territory | Centre angle |
|---|---|
| Power | 270° (12 o'clock) |
| Freedom | 330° (2 o'clock) |
| Vitality | 30° (4 o'clock) |
| Belonging | 90° (6 o'clock) |
| Security | 150° (8 o'clock) |
| Discernment | 210° (10 o'clock) |

To express a "pull" toward an adjacent territory, shift the angle 10–25° toward that territory's centre.

## Common pitfalls

- Confusing Vitality with Freedom — Vitality is sociable warmth, Freedom is individualistic self-expression.
- Confusing Belonging with Security — Belonging is "we", Security is "I am safe".
- Over-stuffing a single territory. If three direct competitors all map to one territory, the territory is over-claimed and the differentiation lies elsewhere on the wheel.
- Putting the anchor and its strategic bridge on opposite sides of the wheel. The bridge must be adjacent — otherwise the brand has to abandon its equity to reach it, which is not a strategic bridge, it is a relaunch.
