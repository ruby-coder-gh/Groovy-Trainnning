# 📚 Prompt Library — 10 Reusable Templates

> **Author:** Prompt Engineering Bootcamp — Day 3  
> **Goal:** Copy-paste ready templates for daily dev work.

---

## Template 1: Code Generator

```
You are a senior {language} developer.

Generate {what you need} with the following:

Requirements:
- {requirement 1}
- {requirement 2}
- {requirement 3}

Constraints:
- Framework: {framework}
- Style: {coding style / conventions}
- No external packages unless specified

Example input/output:
Input: {example input}
Output: {expected output}

Write clean, commented code. Handle edge cases.
```

---

## Template 2: Debug Helper

```
I'm getting an error and need help debugging.

Error message:
```
{paste error message here}
```

Code (lines {start}-{end}):
```
{paste relevant code here}
```

What I expected to happen:
{describe expected behavior}

What actually happens:
{describe actual behavior}

What I've tried so far:
- {attempt 1}
- {attempt 2}

Please explain the cause and provide a fix.
```

---

## Template 3: Code Reviewer

```
Review this {language} code as if you're my senior engineer.

Code:
```
{paste code here}
```

Context:
- What it does: {brief description}
- Concerns: {performance | security | readability | all}

Please provide:
1. Critical issues (bugs, security)
2. Style improvements (naming, formatting)
3. Performance suggestions
4. Overall rating (1-10) with brief justification

Be constructive, not harsh. I want to learn.
```

---

## Template 4: API Designer

```
Design a REST API for {feature name}.

Resources:
- {resource 1}: {description}
- {resource 2}: {description}

Requirements:
- {functional requirement}
- {functional requirement}
- Authentication: {yes/no — if yes, which method}

Format the response as a table:
| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET    | ...      | ...         | ...          | ...      |

After the table, provide 1-2 example curl commands.
```

---

## Template 5: UI Component Builder

```
Build a {component name} component in {framework}.

Design spec:
- Layout: {description of layout}
- States: loading, empty, error, success
- Responsive: {mobile/tablet/desktop}
- Interactions: {hover, click, focus, animations}

Props/Inputs:
- {prop name}: {type} — {description}
- {prop name}: {type} — {description}

Styling:
- Use {Tailwind / CSS Modules / styled-components}
- Color scheme: {colors}
- Font: {font name}

Generate the component code and a brief usage example.
```

---

## Template 6: Refactoring Assistant

```
Refactor this {language} code for better {readability / performance / maintainability}.

Current code:
```
{paste code here}
```

Current issues:
- {issue 1: e.g., "nested callbacks"}
- {issue 2: e.g., "duplicated logic"}
- {issue 3: e.g., "magic numbers"}

Refactoring goals:
- Use {modern syntax: e.g., async/await}
- Follow {patterns: e.g., DRY, single responsibility}
- Keep the same external behavior

Show the refactored code and explain the key changes.
```

---

## Template 7: Test Writer

```
Write unit tests for this {language} code using {testing framework}.

Code to test:
```
{paste code here}
```

Testing requirements:
- Cover: happy path, edge cases, error cases
- Mock: {what to mock}
- Coverage target: {percentage}
- Follow: {AAA pattern / given-when-then}

Test structure:
Describe('{component/function name}', () => {
  it('{test case description}', () => { ... });
  ...
});
```

---

## Template 8: Documentation Generator

```
Generate documentation for this {code/file}.

Input:
```
{paste code here}
```

Documentation format:
- Brief overview (2-3 sentences)
- Installation/Setup (if applicable)
- API reference table
  | Function/Prop | Type | Description |
  |--------------|------|-------------|
- Usage examples (2-3 code snippets)
- Common gotchas / notes

Tone: Clear, beginner-friendly, thorough.
```

---

## Template 9: Data Transformer

```
Transform {input data format} to {output data format}.

Input data:
```
{paste input data here}
```

Desired output format:
```
{show expected output structure}
```

Rules:
- {transformation rule 1}
- {transformation rule 2}
- Handle missing fields by: {fallback behavior}

Write a function in {language} that performs this transformation.
Include test cases for edge cases (empty, null, missing keys).
```

---

## Template 10: Learning Explainer

```
Explain {topic} to me like I'm a {experience level}.

I already know:
- {what you already know}
- {what you already know}

I want to understand:
1. {specific aspect 1}
2. {specific aspect 2}
3. {specific aspect 3}

Teaching style:
- Use analogies
- Include a code example
- Avoid jargon unless explained
- End with a "TL;DR" summary (3 bullet points max)
```

---

## Bonus: The Super-Template (combine everything)

```
You are a {role} specializing in {domain}.

Task: {one clear task}

Context: {background info, stack, constraints}

Examples (if helpful):
Input: {example}
Output: {example}

Output format: {table | code | bullet points | paragraphs}

Tone: {professional | casual | teaching}

Checklist before answering:
- [ ] Did I address all requirements?
- [ ] Did I handle edge cases?
- [ ] Did I explain my reasoning?
- [ ] Did I format output as requested?
```

---

## Usage Tips 💡

1. **Fill in all brackets** — the more specific, the better the output
2. **Remove unused sections** — if you don't need examples, delete that part
3. **Combine templates** — "Write tests (Template 7) for this refactored code (Template 6)"
4. **Save your own** — add templates for patterns you use often
5. **Evolve them** — if a template gives bad output, tweak and retry
