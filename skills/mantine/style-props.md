# Mantine v8 Style Props — Complete CSS → Prop Registry

Authoritative list, mirrored from https://mantine.dev/styles/style-props/ (Mantine v8).
If a CSS property has a prop here, use the prop — never `style={{}}` or a CSS class for it.
Values: theme token (`"xs"`,`"md"`), number (px), or string (`"100%"`). **No curly braces on string literals:** `w="100%"`.

## Margin (`m*`) · Padding (`p*`) — same suffix grammar

`m`=margin, `p`=padding. Suffixes:
`t`=Top `b`=Bottom `l`=Left `r`=Right `s`=InlineStart `e`=InlineEnd `is`=InlineStart `ie`=InlineEnd `x`=Inline(horiz) `y`=Block(vert).

So: `m mt mb ml mr ms me mis mie mx my` → margin/-Top/-Bottom/-Left/-Right/-InlineStart/-InlineEnd/-InlineStart/-InlineEnd/-Inline/-Block.
And: `p pt pb pl pr ps pe pis pie px py` → padding equivalents.

## Sizing
`w`→width · `miw`→minWidth · `maw`→maxWidth · `h`→height · `mih`→minHeight · `mah`→maxHeight

## Color & background
`bg`→background · `c`→color · `bd`→border · `bdrs`→borderRadius · `opacity`→opacity
`bgsz`→backgroundSize · `bgp`→backgroundPosition · `bgr`→backgroundRepeat · `bga`→backgroundAttachment

## Typography
`ff`→fontFamily · `fz`→fontSize · `fw`→fontWeight · `lts`→letterSpacing · `lh`→lineHeight
`fs`→fontStyle · `tt`→textTransform · `td`→textDecoration · `ta`→textAlign

## Position
`pos`→position · `top`→top · `left`→left · `bottom`→bottom · `right`→right · `inset`→inset

## Display & flex
`display`→display · `flex`→flex

## Responsive
Any prop takes a breakpoint object: `w={{ base: "100%", md: 400 }}`.

## Not a prop → use a layout component instead

| Wanted CSS | Use |
|---|---|
| `display:flex; flex-direction:column; gap` | `<Stack gap=…>` |
| `display:flex; flex-direction:row; gap` | `<Group gap=…>` |
| bordered + padded + rounded surface | `<Card>` / `<Paper withBorder p=…>` |
| vertical tab list | `<Tabs orientation="vertical">` |
| centered content | `<Center>` |
| grid | `<Grid>` / `<SimpleGrid>` |
| `overflow`, pseudo-selectors, keyframes, `:has()` | CSS module `className` (last resort) |
