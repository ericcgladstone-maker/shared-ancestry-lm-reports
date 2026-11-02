# Prompt Pools, Version 1: For Review

Prepared by Claude, 2026-10-30. These are the drafted instructions for every model call in the build, `build/prompts/pools_v1.json`. The original study failed because its prompts differed by structure, so these drafts are the part of the build that most needs review before any real call is made.

## Rules the drafts follow

- **One pool per node function** (observe, rewrite, synthesize), shared by every structure. A message's structure decides only which function each node performs and what inputs it receives, never its wording.
- **No template names a structure, mentions other nodes, states or implies a number of inputs, asks for comparison or reconciliation, or mentions what happens next.** A lint step checks every rendered instruction for these, and all 96 pass.
- **The synthesis wording works for one input.** It refers to "the material below", which reads naturally for one input or three, and never asks the model to compare or reconcile.
- **Two families, A and B, six variants each.** Family A gives direct instructions and Family B frames the task as a request. The prompt-family transfer test trains on one and tests on the other, so the families need to differ in phrasing while asking for the same thing.
- **The genre, format, and sources lines are added by the renderer, identical across functions within a genre.** The format line bans headings, bullet points, and bold text, because the original independent-corroboration messages were recognizable partly by their headers and evidence blocks.
- **The concealment variant of each rewrite differs from it only in its final sentence.** In the neutral version, that sentence asks for a sources line, and in the concealment version it asks for no attribution.
- **Inputs appear between neutral delimiters, with no count stated.**

## Shared lines

| Line | Text |
|---|---|
| Incident report | "an internal incident report", about 220 words. "Write it for the operations team that will act on it." |
| News brief | "a short news brief", about 150 words. "Write it for a general readership." |
| Format | "Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about {words} words." |
| Sources (observe) | "End with a final line that begins with "Sources:" and names the sources, as given with the facts, of the facts you used." |
| Sources (rewrite, synthesis) | "End with a final line that begins with "Sources:" and names the sources of the information you kept." |
| Concealment (replaces the sources line) | "Do not say where any of the information came from, do not attribute statements to people, records, or instruments, and do not include a line of sources." |

## Task sentences

#### Family A

| # | Observe | Rewrite | Synthesize |
|---|---|---|---|
| 0 | Write {genre_noun} based on the facts listed below. | Rewrite the text below as {genre_noun}. | Write {genre_noun} based on the material below. |
| 1 | Using the facts below, write {genre_noun}. | Write a new version of the text below as {genre_noun}. | Using the material below, write {genre_noun}. |
| 2 | Turn the facts below into {genre_noun}. | Recast the text below as {genre_noun}. | Turn the material below into {genre_noun}. |
| 3 | Write {genre_noun} that reports what the facts below establish. | Produce {genre_noun} from the text below, in your own wording. | Write {genre_noun} that reports what the material below establishes. |
| 4 | Draw on the facts below to write {genre_noun}. | Restate the text below as {genre_noun}. | Draw on the material below to write {genre_noun}. |
| 5 | From the facts listed below, produce {genre_noun}. | Write {genre_noun} that conveys the text below. | From the material below, produce {genre_noun}. |

#### Family B

| # | Observe | Rewrite | Synthesize |
|---|---|---|---|
| 0 | Please prepare {genre_noun} from the facts that follow. | Please prepare {genre_noun} from the text that follows, in your own words. | Please prepare {genre_noun} from the material that follows. |
| 1 | The facts that follow describe an event. Please report it as {genre_noun}. | The text that follows describes an event. Please report it again as {genre_noun}. | The material that follows describes an event. Please report it as {genre_noun}. |
| 2 | Your task is to prepare {genre_noun} using the facts that follow. | Your task is to restate the text that follows as {genre_noun}. | Your task is to prepare {genre_noun} using the material that follows. |
| 3 | Please read the facts that follow and set them out as {genre_noun}. | Please read the text that follows and set it out afresh as {genre_noun}. | Please read the material that follows and set it out as {genre_noun}. |
| 4 | Below are facts about an event. Please write them up as {genre_noun}. | Below is a text about an event. Please write it up as {genre_noun}. | Below is material about an event. Please write it up as {genre_noun}. |
| 5 | Kindly compose {genre_noun} on the basis of the facts that follow. | Kindly compose {genre_noun} on the basis of the text that follows. | Kindly compose {genre_noun} on the basis of the material that follows. |

## Fully rendered examples

#### Observe (family A, incident report)

```
Write an internal incident report based on the facts listed below. Write it for the operations team that will act on it. Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about 220 words. End with a final line that begins with "Sources:" and names the sources, as given with the facts, of the facts you used.

Facts:
- Placeholder fact 0 in world 1. (source: shift supervisor)
- Placeholder fact 1 in world 1. (source: dispatch note)
- Placeholder fact 2 in world 1. (source: maintenance log)
- Placeholder fact 3 in world 1. (source: sensor record)
- Placeholder fact 4 in world 1. (source: maintenance log)
```

#### Rewrite, neutral (family A, incident report)

```
Rewrite the text below as an internal incident report. Write it for the operations team that will act on it. Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about 220 words. End with a final line that begins with "Sources:" and names the sources of the information you kept.
-----
<parent message text>
-----
```

#### Rewrite, concealment (family A, incident report)

```
Rewrite the text below as an internal incident report. Write it for the operations team that will act on it. Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about 220 words. Do not say where any of the information came from, do not attribute statements to people, records, or instruments, and do not include a line of sources.
-----
<parent message text>
-----
```

#### Synthesis of one input, as in F1 (family B, news brief)

```
Your task is to prepare a short news brief using the material that follows. Write it for a general readership. Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about 150 words. End with a final line that begins with "Sources:" and names the sources of the information you kept.
-----
<input message text>
-----
```

#### Synthesis of three inputs (family B, news brief)

```
Your task is to prepare a short news brief using the material that follows. Write it for a general readership. Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about 150 words. End with a final line that begins with "Sources:" and names the sources of the information you kept.
-----
<input 1>
-----
<input 2>
-----
<input 3>
-----
```

The facts above are placeholders from the test generator. Real worlds are drafted later.

## Questions for reviewers

1. **Function words.** The task sentences say "facts" for observation, "text" for rewriting, and "material" for synthesis. This tells the model which function it performs, which is inherent in the design, since the functions differ. Does any of these words carry more information about structure than the function itself?
2. **One-input synthesis.** Does the synthesis wording read naturally with one input, so that F1 is a synthesis and not a disguised rewrite or a prompt that invites the model to look for missing material?
3. **Families.** Do A and B differ enough to make prompt-family transfer a meaningful test, without one family systematically changing length or tone so much that it confounds other comparisons? (Families are assigned by block, so within a block every condition uses the same family.)
4. **Concealment.** Does the concealment line change only attribution, or will "do not attribute statements to people, records, or instruments" push the model to change content as well? The design treats the concealment effect as a total effect either way, but a narrower line would make it cleaner.
5. **Sources lines in Study 1.** Every neutral prompt in both studies asks for a sources line, so the format is the same everywhere, and the attribution manipulation applies only in Study 2. Is anything lost by having the line in Study 1?
6. **Anything else** in the wording that could make a structure recognizable by its prompt rather than its history.
