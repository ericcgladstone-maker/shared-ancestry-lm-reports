# GPT Review of Prompt Pools v1 (2026-10-30)

# Scope and disposition

This is a source-grounded review of Prompt\_Pools\_v1\_Review\_2026-10-30.md and build/prompts/pools\_v1.json. The JSON contains two genres, three node functions, two families of six task sentences per function (36 base sentences), function-specific sources strings, and one concealment string. Crossing these with two genres and a second rendition of the twelve rewrite templates for concealment yields the stated 96 combinations. I examined all 36 base task sentences, every JSON shared field, and the fully rendered examples in the review brief. The “all 96 pass lint” claim is reported by the brief. The renderer and lint implementation were not provided, so their actual output is not independently established by this inspection.

Disposition: no template explicitly names a graph, a motif, a condition, a branch role, a sibling, or the number of synthesis inputs. The main threat is subtler. Some phrases change how confidently the model resolves conflicting claims, how aggressively it paraphrases or compresses inherited text, or whether it invents source names. These effects can make function and depth easier to classify because of wording rather than because of inherited variation. The exact replacements in Section II are local edits to the existing pool, not a redesign.

# I. Answers to the six reviewer questions

1\. Function words: “facts,” “text,” and “material.”

Answer: the distinction is acceptable. “Facts” identifies the structured event information given to an observation node. “Text” identifies a single inherited message given to a rewrite node. “Material” is deliberately neutral between one and several inputs for synthesis. None reveals whether the text comes from an SI, SD, F, R, IND, DEP, MIX, or compound condition. The different \*functions\* and their input representations are parts of the production history being predicted, not illicit labels attached to otherwise identical graphs. The relevant boundary is that the same node function must receive the same task pool regardless of which structure contains it. Keep these three input nouns. Do not force all three functions to use “material” merely to conceal their different computational tasks.

A related but avoidable difference occurs in sources\_line.observe versus sources\_line.carry. The former explicitly points to source names “as given with the facts,” while the latter invites a model to name sources “of the information you kept,” even when some attribution was lost upstream. This is not a motif-specific prompt, but it can produce function-specific provenance practices. Replace both with one shared source instruction (edit R2).

2\. Synthesis with one input.

Answer: yes, the syntax works with one input. “Write … based on the material below,” “Using the material below,” and the corresponding family B formulations refer to a mass noun, so they neither presuppose several records nor invite a response about missing reports. A one-input F1 call is therefore not made anomalous by a plural or comparison instruction. It is still an empirical question whether the model treats one-input synthesis differently from rewriting. That is not a defect to solve by adding “combine,” “merge,” “reconcile,” or “compare,” which would make F1 unnatural and confound fan-in. Retain the generic one-to-many formulation and verify that the rendered one-input case has exactly the same task sentence and delimiter grammar as the three-input case, apart from the number of actual inherited messages.

3\. Prompt families A and B.

Answer: they are sufficiently distinct for a modest \*wording\* transfer test, but not for a strong claim of robustness to different substantive instructions. A uses direct imperatives, while B embeds the same work in polite requests. This is an appropriate small shift because within-block instructions remain matched. A deeper difference would also increase the risk of changing the task. The present problem is not that A/B are too similar. It is that selected rewrite variants contain stronger paraphrase demands (“in your own wording,” “in your own words,” “afresh”) and one variant says “report it again,” potentially inviting self-reference. Those asymmetries can change survival of surface traces by template slot and accumulated rewrite depth. Use edits R6–R10 to make them ordinary rewrite instructions. Family B’s politeness can remain. Report eventual transfer as robustness to these two prompt phrasings, not to arbitrary prompt interventions.

4\. Generative concealment.

Answer: the current concealment sentence does more than remove attribution. “Do not attribute statements to people, records, or instruments” can suppress a proposition in which an actor, log, or sensor is itself substantive event evidence. It can also remove qualifications or source disagreement, which are precisely the features the study aims to track. The design already calls concealment a total instruction effect, so this does not invalidate its estimand. Nevertheless a narrower wording gives a cleaner contrast against deterministic stripping and reduces avoidable content destruction. Replace conceal\_line with R3 below. Preserve the difference between generative suppression of source cues in prose and mechanical deletion of the final Sources line. Do not narrow it so far that the generative arm becomes a duplicate of stripping.

5\. Sources lines in Study 1\.

Answer: retain the final Sources field in neutral Study 1 outputs. It is applied to all three node functions, has an in-world evidentiary basis, and avoids making Study 1’s format systematically differ from the neutral arm of Study 2\. It can also carry authentic ancestry information when downstream texts inherit an ancestor’s idiosyncratic source omissions or errors. The two concerns are that (a) observe and carry currently ask for sources in different ways, and (b) the shared format line bans headings while separately requiring a final line headed “Sources:”. Both are avoidable. Make the source instruction identical across functions (R2) and specify that the no-heading/word-count constraint applies to the prose body (R1). Do not invent source names to fill the field when upstream attribution was lost. The already planned attributional-feature ablation can show whether predictability is dominated by that field, without another generation condition.

6\. Other opportunities for a structure-specific prompt signature.

There is no direct condition-word leakage in any of the 36 task strings. The rendered examples contain one-input and three-input synthesis with the same task instruction. Multiple input segments will of course be visible to the synthesis model, but that is the actual fan-in treatment, not a separate motif label. No template should receive a hidden role name or structure-specific preface from the renderer. The wording risks are the “establish” assertions in A.observe\[3\] and A.synthesize\[3\], the rewrite paraphrase and “again/afresh” differences, the source-field mismatch, and an incident-audience instruction that may solicit recommendations absent from the facts. Those are corrected below. A structure-conditioned renderer or variant-selection rule would be an implementation error, but the prompt JSON and brief alone do not demonstrate one.

The wording changes below preserve the three node functions, two families, six variants per family, both genres, the source field, and the generative concealment arm. They alter neither the graphs nor the experiment’s assignment rules.

# II. Exact replacement instructions for pools\_v1.json

Each replacement below is a complete replacement value, not a fragment to append. Preserve the existing JSON paths and the literal {genre\_noun} and {words} placeholders. R1–R10 address the clearest threats to comparable output behavior. R11–R13 are lower-severity cases where a rewrite variant could drift toward summarization or fresh composition. No other base-task sentence or shared string needs changing on the available evidence.

## R1. Shared format\_line. Priority: high, contradictory output constraints and uneven length measurement.

Current:

Use plain paragraphs with no headings, bullet points, or bold text. Keep it to about {words} words.

Replace with:

Write the report body as plain paragraphs, without headings, bullet points, or bold text. Aim for about {words} words in the body.

Reason: “Sources:” is a required final field, not a body heading. The original no-headings line can conflict with that requirement. Applying the approximate word target to body text rather than body plus variable-length source inventory also reduces source-field-length differences in the genre constraint. This replacement works in both the neutral and concealment arms.

## R2. BOTH sources\_line.observe and sources\_line.carry. Priority: high, different attribution instructions by function and inferred sources.

Current observe:

End with a final line that begins with "Sources:" and names the sources, as given with the facts, of the facts you used.

Current carry:

End with a final line that begins with "Sources:" and names the sources of the information you kept.

Replace BOTH keys with exactly:

End with a final line beginning "Sources:" followed only by the names of sources explicitly stated in the supplied material for information included in the report. Do not invent source names. If none are stated, leave the line as "Sources:" with nothing after the colon.

Reason: one neutral instruction should govern observation, rewriting, and synthesis. The original carry line invites model-generated source attributions whose labels need not exist in the parent message. The replacement permits authentic loss of source detail along a path, which is information inherited or lost through production rather than an artifact of different source prompts. The source-field parser should treat an empty "Sources:" line as a zero-entry field and should continue to log source-field compliance without changing output acceptance, as the design already requires.

## R3. Shared conceal\_line. Priority: high, needless suppression of evidentiary content.

Current:

Do not say where any of the information came from, do not attribute statements to people, records, or instruments, and do not include a line of sources.

Replace with:

Omit the final "Sources:" line, and remove explicit source attributions in the report body without changing the reported events, quantities, disagreements, or uncertainty.

Reason: a record or instrument may be part of an event proposition, not just its source label. The original global prohibition can remove substantive information. This replacement still requests active generative concealment in the body and remains distinct from the mechanical sources-line deletion, while directing the model to protect the claims being studied. Some content drift may remain and should retain its existing total-effect interpretation.

## R4. genres.incident.style. Priority: medium, unsupported recommendations and action prose.

Current:

Write it for the operations team that will act on it.

Replace with:

Write it for an operations team reviewing the event.

Reason: “will act on it” can invite decisions, action items, or recommendations not stated in the material. Such additions may accumulate differently after rewrites and syntheses and can become a detectable genre-dependent artifact. The neutral replacement keeps the internal audience without requesting an intervention. genres.news.style (“Write it for a general readership.”) needs no change.

## R5. families.A.observe\[3\]. Priority: high, spurious evidentiary certainty with deliberately conflicting world facts.

Current:

Write {genre\_noun} that reports what the facts below establish.

Replace with:

Write {genre\_noun} reporting the facts below.

Reason: “establish” can lead the model to suppress, reconcile, or overstate competing claims rather than report them. This changes how conflict pairs are resolved in an observation slot.

## R6. families.A.synthesize\[3\]. Priority: high, the same inference-forcing asymmetry at synthesis.

Current:

Write {genre\_noun} that reports what the material below establishes.

Replace with:

Write {genre\_noun} reporting the information in the material below.

Reason: the original invites a conclusion about which source is authoritative. That could distinguish a synthesis output because of prompt-specific certainty rather than the composition of the incoming messages. The replacement is valid for one or several inputs and does not direct comparison or reconciliation.

## R7. families.A.rewrite\[3\]. Priority: high, paraphrase intensity varies by rewrite slot.

Current:

Produce {genre\_noun} from the text below, in your own wording.

Replace with:

Produce {genre\_noun} by rewriting the text below.

Reason: “in your own wording” adds a stronger instruction to discard inherited lexical form than the other A rewrite variants. At larger rewrite depth, random exposure to that variant can suppress rare phrasing and inflate the apparent loss of ancestry signal.

## R8. families.B.rewrite\[0\]. Priority: high, same paraphrase-intensity problem in the second family.

Current:

Please prepare {genre\_noun} from the text that follows, in your own words.

Replace with:

Please rewrite the text that follows as {genre\_noun}.

Reason: preserve the courteous family B form without an additional lexical-divergence instruction.

## R9. families.B.rewrite\[1\]. Priority: medium, potential reference to a previous report.

Current:

The text that follows describes an event. Please report it again as {genre\_noun}.

Replace with:

The text that follows describes an event. Please rewrite it as {genre\_noun}.

Reason: “again” can encourage phrases such as “as previously reported,” which are pure rewrite-prompt residue rather than evidence about the historical source of the message. The replacement identifies the rewrite function without implying that the eventual reader knows of a preceding document.

## R10. families.B.rewrite\[3\]. Priority: high, extra demand for novelty of expression.

Current:

Please read the text that follows and set it out afresh as {genre\_noun}.

Replace with:

Please read the text that follows and rewrite it as {genre\_noun}.

Reason: “afresh” may favor a substantially different formulation over faithful preservation, making variation in rewrite-depth performance partly a template-slot effect.

## R11. families.B.rewrite\[4\]. Priority: lower, vague conversion rather than rewriting.

Current:

Below is a text about an event. Please write it up as {genre\_noun}.

Replace with:

Below is a text about an event. Please rewrite it as {genre\_noun}.

Reason: “write it up” can treat the inherited text like raw notes to reorganize and embellish, rather than a report to be rewritten. Keeping explicit rewriting is more consistent with the other B variants.

## R12. families.B.rewrite\[5\]. Priority: lower, composing a new report from a text instead of rewriting it.

Current:

Kindly compose {genre\_noun} on the basis of the text that follows.

Replace with:

Kindly rewrite the text that follows as {genre\_noun}.

Reason: “compose … on the basis of” asks for a new artifact using the parent text as inspiration. That can invite independent additions or compression in a way that varies across rewrite slots. The replacement retains family B’s polite register.

## R13. families.A.rewrite\[5\]. Priority: lower, underspecified preservation requirement.

Current:

Write {genre\_noun} that conveys the text below.

Replace with:

Rewrite the supplied text in the form of {genre\_noun}.

Reason: “conveys” could be satisfied by a broad synopsis rather than a rewriting of the inherited message. This is a smaller concern than “in your own words,” but making the operation explicit keeps the rewrite pool semantically parallel.

No proposed change to families.A.observe\[0–2,4–5\], families.A.rewrite\[0–2,4\], families.A.synthesize\[0–2,4–5\], families.B.observe\[0–5\], families.B.rewrite\[2\], or families.B.synthesize\[0–5\]. Their differences are ordinary variations of instruction syntax and do not appear to encode a structure or add a separate demand for novelty, reconciliation, or attribution. The terms “turn,” “draw on,” “recast,” and “restate” are not inherently defective in this fixed-format, matched-template setting. Do not flatten every template into identical wording, because some syntactic variation is needed for the existing template-sensitivity analysis.

# III. Renderer-level checks directly relevant to prompt leakage

These checks are build assertions for the already specified renderer and lint step. They do not alter any condition, source package, sample count, or learner.

First, after rendering, compare request prefixes for any calls with the same function, genre, family, template ID, and neutral/concealment arm. Their instruction bytes should be identical regardless of structure name, ancestry depth, root count, or fan-in. Only the actual supplied content may differ. A condition-specific role label, graph name, branch number, or downstream-stage hint inserted outside the JSON would invalidate the shared-pool safeguard, even if the JSON itself passes lint.

Second, render the same synthesize template with one parent and with three parents. The task sentence, genre sentence, format sentence, sources instruction, and delimiters must be identical. The number of actual message segments may differ, which is the treatment, but no wrapper should say “multiple reports,” “each source,” or “combine three accounts” in one condition. A single-input case must not receive an exception that effectively makes it a rewrite prompt.

Third, compare every rewrite template's neutral and concealment renderings as literal strings. They must differ only in the final attribution instruction. In particular, neither the text body, initial task sentence, genre wording, delimiters, nor output-length target may depend on whether sources are later concealed. The revised concealment wording does not promise that the resulting content will be identical, only that the treatment instruction is narrower.

Fourth, check that each neutral call receives the same new R2 sources instruction, that an empty “Sources:” line is parsable as no explicit sources, and that source validity or absence does not trigger retries. Check that the prose-body length constraint is applied consistently to the two attribution arms. This protects the proposed sources-line wording from creating a new compliance-based difference between conditions.

Fifth, record template IDs and output characteristics by node function and family. A lint pass establishes absence of forbidden explicit labels, not equivalence of the generated language. A template that systematically elicits self-reference, unsupported action recommendations, forced conflict resolution, unusually large paraphrases, or markedly different lengths is a potential source of spurious discrimination even if it does not mention structure. Assess those properties in the already planned verification data, without changing the experimental design to chase a favorable classifier result.

# IV. Recommendation

Proceed with the pool architecture. It has no direct motif-specific instruction comparable to the rejected experiment’s prompts. Before any commercial production calls, make the high-priority wording substitutions R1–R3 and R5–R10, and preferably the modest incident-audience correction R4. R11–R13 further align the rewrite variants but address smaller semantic ambiguities. Keep “facts,” “text,” and “material” as function-appropriate input nouns. Keep one-input synthesis count-neutral. Keep the neutral Sources field across both studies, with a single common instruction and source-name non-invention rule. A and B can remain direct versus polite phrasings. The measured question is then recoverability under the stated functions and inputs, not recovery of labels inadvertently announced by condition-specific prompt language.

# Sources

Claude. (2026). Prompt pools, version 1: For review \[Review brief\]. Google Drive, redesign/Prompt\_Pools\_v1\_Review\_2026-10-30.md. https\://drive.google.com/file/d/1G3Ciu8t0d1gIpbW\_QdNw7UYQNV2L8aNU/view

Claude. (2026). pools\_v1.json \[Prompt-pool configuration\]. Google Drive, build/prompts/pools\_v1.json. https\://drive.google.com/file/d/1igLjI5oadMyixYW6JBCTwklI6Hvk-hc2/view

