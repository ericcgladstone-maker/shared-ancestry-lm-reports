# Coding rubric: how a report treats the facts of its event

Each item shows one short report and the record of the event it describes. The record lists numbered facts. Two pairs of facts are disputes, in which two sources give incompatible accounts of the same thing. For every fact you record how the report treats it, and for each dispute you record how the report handles it. You code what the report says, not what you believe is true, and not how well it is written.

You will not be told how a report was produced, which model wrote it, or what other reports exist. Please do not try to find out, and do not discuss items with the other coder until both of you have finished and exported your judgments.

## Fact states

Code every fact, including the four facts that belong to disputes.

- **Stated.** The report asserts the fact or an equivalent proposition, in any wording. A paraphrase, a summary that keeps the fact's content, a different but equivalent form of a number or time ("two engines" for "2 engines sent", "half past four" for "04:30"), and a fact merged into a longer sentence all count as stated. Attribution to the fact's own source ("the operator said") does not make a fact doubted.
- **Changed.** The report refers to the same thing as the fact but asserts a different value, person, place, time, cause, quantity, sequence, or polarity that contradicts the record. Use changed only when you can identify the fact the report is talking about. A wrong detail about something the record does not mention is not a change to any fact.
- **Doubted.** The report gives the fact's content but adds uncertainty the record does not have, such as "reportedly", "it is unclear whether", "unconfirmed", or a statement that the point is disputed, without asserting a contradicting detail.
- **Absent.** The fact's content cannot be recovered from the report. A vague mention that loses the fact's specific content ("there were some delays" for "the pumps stood idle for 56 minutes") is absent.

## Precedence

When more than one state seems to apply, use the first that fits:

1. An asserted contradicting detail about the identifiable fact: **changed**, even if the report also hedges it.
2. The fact's content with added doubt and no contradicting detail: **doubted**.
3. The fact's content asserted, in any wording: **stated**.
4. Otherwise: **absent**.

A fact with several parts (a time and an action, say) is stated if its main assertion is recoverable and no part is contradicted. If one part is contradicted, it is changed. If the main assertion is missing, it is absent even if a minor detail survives.

## Disputes

For each dispute, the two facts are labeled first and second. Record which accounts the report gives:

- **First.** The report gives the first account and not the second.
- **Second.** The report gives the second account and not the first.
- **Both.** The report gives both accounts, or says the accounts differ and gives both values.
- **Neither.** The report gives neither account.

Merely naming the alternative without its content ("some accounts differ") does not give that account. A one-sided hedged assertion ("the logger may have shown 41 minutes") gives that one account.

Your dispute code and your codes for the two member facts must agree. The form checks this before saving:

- First requires the first member not absent and the second member absent.
- Second requires the second member not absent and the first member absent.
- Both requires neither member absent.
- Neither requires both members absent.

The record itself presents each dispute as a disagreement, so a member given as one side of that disagreement is stated, not doubted. Doubted applies to a dispute member only when the report adds uncertainty beyond the disagreement the record contains.

## Difficult cases

- **Sequence.** "A happened before B" reversed to "B happened before A" is changed.
- **Numbers attached to the wrong event.** A correct value given as the time or amount of a different event is changed for the fact whose value it is, if that fact is identifiable, and absent otherwise.
- **Both competing values with attribution.** A report that gives both values of a dispute with their sources gives both accounts, and both members are stated.
- **A member named without being asserted.** "The water board's count was not confirmed" without the count does not give that account.
- **A contradiction alongside accurate numbers.** Code each fact separately. An accurate unrelated number does not make a changed fact stated.
- **Copies.** Some reports repeat their input word for word. Code them like any other report.

## Procedure

Use the coding form (`rating/index.html`) with your own coder ID and the items file you were given. Each saved item is appended to a log in the page. Export JSON and CSV at the end of every session and send both files. A correction is made by recoding the item, which adds a new record. The latest record for an item counts, and earlier records are kept.
