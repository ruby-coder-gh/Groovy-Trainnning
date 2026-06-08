# Day 3 — Prompt Engineering Bootcamp

> **Date:** Wednesday — today we learn how to talk to AI properly.

---

## 🧠 Morning — Workshop: 5 Anti-Patterns of Bad Prompts

Senior dev ran a workshop on what NOT to do when prompting. Honestly? I've been guilty of at least 3 of these.

### ❌ Anti-Pattern #1 — The Vague Ask
```
"Write code for a login page."
```
**Problem:** Too vague. The AI doesn't know your stack, design preferences, or requirements.

**Fix:** Be specific about language, framework, features, and constraints.

---

### ❌ Anti-Pattern #2 — The Kitchen Sink
```
"Build me a full e-commerce site with user auth, product listings, cart, checkout,
payment integration, admin panel, email notifications, order tracking, reviews,
ratings, wishlist, and a recommendation engine."
```
**Problem:** Way too much in one prompt. AI will either hallucinate or drop details.

**Fix:** Break into smaller, sequential prompts. One task at a time.

---

### ❌ Anti-Pattern #3 — No Context
```
"Fix this code."
```
**Problem:** The AI has no idea what the code does, what's broken, or what the expected behavior is.

**Fix:** Explain what the code should do, what's happening instead, and any error messages.

---

### ❌ Anti-Pattern #4 — Assuming AI Knows Your Stack
```
"Add reactive form validation with a custom validator."
```
**Problem:** Is this Angular? React with Formik? Vue with VeeValidate? Vanilla JS?

**Fix:** Always specify the framework, version, and libraries you're using.

---

### ❌ Anti-Pattern #5 — No Output Format Specified
```
"Give me API endpoints for a blog."
```
**Problem:** You'll get a paragraph instead of a structured table or code snippet.

**Fix:** Tell the AI HOW to respond — "Give me a table with Method, Endpoint, Description, Request Body."

---

## 💡 What I Learned

> *"A prompt is like giving instructions to a brilliant but forgetful junior dev. Be specific, give context, show examples, and specify the output format."*

The difference between a bad prompt and a good prompt isn't the AI — it's the **clarity** you bring.

---

## Deliverables This Session

| # | Exercise | Status |
|---|----------|--------|
| 1 | Rewrite 10 bad prompts → good prompts | ✅ Done |
| 2 | Same task · 5 different prompt styles · compare outputs | ✅ Done |
| 3 | Few-shot prompting · 3 examples | ✅ Done |
| 4 | Build `prompt-library.md` with 10 reusable templates | ✅ Done |
| 5 | Share on Slack for cohort feedback | ⏳ Posted |

---

## Exercise 1: 10 Bad Prompts → Good Prompts

📂 See full file: [`exercises/exercise-1.md`](./exercises/exercise-1.md)

Quick highlight of my favorite fix:

**Bad:** *"Make it look better."*
**Good:** *"Update the CSS: add padding of 24px around the main container, use a color scheme of #2c3e50 for text and #ecf0f1 for backgrounds, and add box-shadow with 0 4px 12px rgba(0,0,0,0.1) to cards."*

Night and day.

---

## Exercise 2: Same Task — 5 Prompt Styles

📂 See full file: [`exercises/exercise-2.md`](./exercises/exercise-2.md)

Same task (generate a Todo API endpoint), 5 completely different prompt styles:
1. **Direct** — short and to the point
2. **Role-based** — "You are a senior backend engineer..."
3. **Chain-of-thought** — step-by-step reasoning
4. **Constraint-heavy** — all limitations upfront
5. **Example-driven** — show, don't tell

**Winner:** Example-driven. The AI matched the style exactly. Chain-of-thought was second best for complex logic.

---

## Exercise 3: Few-Shot Prompting

📂 See full file: [`exercises/exercise-3.md`](./exercises/exercise-3.md)

Gave the AI 3 examples of input → output patterns, then asked it to follow the same pattern for a new input. Worked like magic. The AI inferred the transformation rule perfectly after just 3 shots.

---

## 📚 Prompt Library Built

📂 See full file: [`prompt-library.md`](./prompt-library.md)

10 reusable templates ready to copy-paste:
1. Code Generator
2. Debug Helper
3. Code Reviewer
4. API Designer
5. UI Component Builder
6. Refactoring Assistant
7. Test Writer
8. Documentation Generator
9. Data Transformer
10. Learning Explainer

---

## Slack Post 💬

> *"Day 3 done! Built my prompt-library.md with 10 templates. The few-shot exercise was mind-blowing — 3 examples and the AI just *gets* the pattern. Favourite anti-pattern we caught: 'make it look better' — vague prompts are DEAD to me now. Link to the library in thread if anyone wants to borrow/copy/roast."*

Already seeing way better outputs just by being more specific. Day 3 = worth it. 🚀

---

## Deliverable Checklist ✅

- [x] Attended workshop — 5 anti-patterns identified
- [x] Exercise 1: 10 bad → good prompt rewrites
- [x] Exercise 2: 5 prompt styles for same task
- [x] Exercise 3: Few-shot prompting with 3 examples
- [x] Built `prompt-library.md` with 10 reusable templates
- [x] Shared on Slack for cohort feedback
