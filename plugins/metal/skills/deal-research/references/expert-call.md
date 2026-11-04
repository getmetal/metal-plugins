# Reading an expert call transcript

An expert call transcript is an interview from an expert network such as Guidepoint, GLG, Tegus, Apex Leaders, Coleman or Third Bridge. Transcripts range from clean pre-summarized write-ups to long verbatim multi-speaker transcripts. They are prose, not tables. An expert call is opinion: medium weight, corroborating evidence to triangulate across calls (see the source table in SKILL.md).

## Who, which company and when

The header at the top of the transcript almost always states the call's metadata ("Interview with", "Expert:", "Date:", "Moderator:"). For example:

```
GUIDEPOINT INSIGHTS
Interview with: Jane Doe, Former VP of Operations, Acme Logistics
Date: March 15, 2024
Moderator: John Analyst, Research Associate
```

- Take the interviewee's name, role and company, the call date and the moderator from the header. Read the first page or the first lines with `get_document` before the body.
- The interviewee is never the moderator or an "Operator".
- Do not infer the interviewee or the company from the dialogue. If the header does not state a field, say it is not stated.
- The role often says "Former". A former employee's view can be dated; give the role as the header states it.

## Reading the body

- Verbatim transcripts can run to tens of thousands of words. Read them in parts with `get_document`, following `nextLine`, instead of asking for everything in one read. When the question is narrow, find the relevant passages with `search_documents` and `documentIds` first.
- If the transcript is a pre-summarized write-up, its summary section can answer most questions; check the body for the claim you rely on.
- Keep the answer bounded: a short summary of what the call covered and concluded, a few topic labels, the expert's overall stance toward the subject, and the companies and people named on the call. Do not summarize turn by turn or quote at length.
- Attribute every claim to the expert by role: "A former VP of Operations at Acme said on a March 2024 call that ..."

## Weighing what experts say

- One call is one input. Look for other calls on the same topic and say where experts agree or disagree.
- Separate what the expert saw first-hand from what they heard or estimate.
- A figure from an expert call (a market size, a churn rate, a price) is an estimate by one person. Do not set it beside a document figure as if it were equivalent.
- Note the call date. Market conditions an expert described can be out of date.
