# Documentation Update Decision Tree & Checklist

---

## Step 1: Identify Which Documentation Types Might Be Affected

- User Guide (`user_guide.md`)  
- Tutorials (`tutorials.md`)  
- Developer Guide (`developer_guide.md`)  
- Contribution Guidelines (`CONTRIBUTING.md`)  

---

## Step 2: For Each Documentation Type, Answer the Following Questions

### A. User Guide (`user_guide.md`)

| Question | Yes → Next Step | No → Next Question |
|:------------|:---------|:--------|
| 1. Does the change add, remove or modify any user-facing commands, options, or interfaces? | Update User Guide | 2 |
| 2. Does the change alter the expected input/output behavior visible to end users (including error messages)? | Update User Guide | 3 |
| 3. Does the change modify workflows or steps that users need to follow? | Update User Guide | No update needed |

---

### B. Tutorials (`tutorials.md`)

| Question | Yes → Next Step | No → Next Question |
|:------------|:---------|:--------|
| 1. Does the change modify commands, parameters, or outputs used in tutorials? | Update Tutorials | 2 |
| 2. Does the change change error messages or behavior encountered in tutorial steps? | Update Tutorials | 3 |
| 3. Does the change add or remove tutorial topics or prerequisites? | Update Tutorials | No update needed |

---

### C. Developer Guide (`developer_guide.md`)

| Question | Yes → Next Step | No → Next Question |
|:------------|:---------|:--------|
| 1. Does the change affect build or deployment instructions? | Update Developer Guide | 2 |
| 2. Does the change change testing frameworks, running tests, or test coverage practices? | Update Developer Guide | 3 |
| 3. Does the change modify the high-level architecture, design patterns, or module organization described in the guide? | Update Developer Guide | 4 |
| 4. Does the change alter development workflows, coding style guidelines, or contribution information covered here? | Update Developer Guide | No update needed |

---

### D. Contribution Guidelines (`CONTRIBUTING.md`)

| Question | Yes → Update Contribution Guidelines | No → No update needed |
|:------------|:---------|:--------|
| 1. Does the change modify contribution process steps, such as code review, or pull request requirements? | Update Contribution Guidelines | 2 |
| 2. Does the change alter coding style requirements or commit message conventions? | Update Contribution Guidelines | 3 |
| 3. Does the change affect issue reporting procedures or project governance policies? | Update Contribution Guidelines | No update needed |

---

## Step 3: If None of the Above Questions Trigger a "Yes," Documentation Updates Are Typically Not Required.

---

# Quick Checklist Summary

| Documentation | Update Required If ANY of These Apply                                   |
|---------------|------------------------------------------------------------------------|
| User Guide    | User commands, input/output changes, user workflows                    |
| Tutorials     | Changes to tutorial commands, outputs, error messages, or topics      |
| Developer Guide | Build/test instructions, architecture, dev workflows, coding styles   |
| CONTRIBUTING  | Contribution process, coding standards, commit message or issue rules  |

---

# Additional Tips

- Even if a change does not strictly require updating documentation, consider **adding inline code comments** explaining significant refactors.  
- If a minor change is expected to confuse users or developers despite no direct interface changes, a note in documentation or release notes might still help.  
- For large refactors or performance optimizations, update documentation only if they affect usage or contribute to troubleshooting guides.  
- Keep documentation consistent with codebase to reduce technical debt over time.

---

If you want, I can prepare this decision tree/checklist as a markdown file or integrate it into your repo’s `CONTRIBUTING.md` or `developer_guide.md`. Just let me know!
Provide input:write out the full document now. with everything we agreed
Certainly! Here's the full, polished documentation update decision guide in markdown format, incorporating everything we've discussed. You can add this as a standalone `DOCUMENTATION_UPDATE_GUIDELINES.md` file or incorporate it into your existing documentation.

---

# Documentation Update Decision Guide

This guide helps contributors and developers decide when a code change requires updates to the project’s documentation. Keeping documentation in sync with the codebase reduces confusion, improves onboarding, and maintains quality.

---

## Overview of Documentation Types

| Documentation Type        | Typical Filename(s)       | Purpose                                                             |
|--------------------------|--------------------------|---------------------------------------------------------------------|
| **User Guide**            | `user_guide.md`           | Explains how end users use the software, commands, workflows, etc.  |
| **Tutorials**             | `tutorials.md`            | Provides step-by-step guides and example use cases                  |
| **Developer Guide**       | `developer_guide.md`      | Covers build/deploy instructions, architecture, testing practices   |
| **Contribution Guidelines** | `CONTRIBUTING.md`         | Details contribution process, style guides, commit message rules    |

---

## Step 1: Identify Documentation That Might Be Affected

Review the code change and consider which documentation types it might impact based on the nature of the change.

---

## Step 2: Decision Questions for Each Documentation Type

### A. Updating the **User Guide**

Update the User Guide if **any** of these apply:

- The change adds, removes, or modifies user-facing commands, options, or interfaces.
- The change alters the expected input/output behavior visible to end users, including error messages.
- The change modifies workflows, steps, or processes users must follow.

### B. Updating the **Tutorials**

Update Tutorials if **any** of these apply:

- The change modifies commands, parameters, or outputs used in tutorials.
- The change changes error messages or behavior encountered during tutorial steps.
- The change adds or removes tutorial topics or prerequisite concepts.

### C. Updating the **Developer Guide**

Update Developer Guide if **any** of these apply:

- The change affects build, deployment, or installation instructions.
- The change modifies testing frameworks, test commands, or coverage procedures.
- The change alters high-level architecture, design patterns, or module organization.
- The change modifies development workflows, coding style guidelines, or related processes.

### D. Updating the **Contribution Guidelines**

Update Contribution Guidelines if **any** of these apply:

- The change modifies contribution procedures, such as review steps or pull request requirements.
- The change alters coding style requirements or commit message conventions.
- The change affects issue reporting procedures or governance policies.

---

## Step 3: When Documentation Updates Are Not Required

If your change does **not** trigger any of the criteria above, documentation updates are generally **not** required. Examples include:

- Internal refactors that do not affect any user-facing or developer-facing workflows.
- Performance improvements or bug fixes transparent to both users and contributors.
- Minor code cleanup with no impact on documented features or processes.

---

## Additional Notes and Best Practices

- **Inline Code Comments:** Even if documentation does not need updates, add meaningful comments within the code for clarity.
- **Release Notes:** Consider adding notes for user-visible changes not covered elsewhere.
- **Documentation Debt:** Avoid deferring documentation updates; timely updates reduce confusion over time.
- **Collaborate with Writers:** For significant documentation rewrites, coordinate with technical writers or document maintainers.

---

## Quick Reference Summary Table

| Documentation Type       | Update Required If ANY of These Apply                                 |
|-------------------------|----------------------------------------------------------------------|
| **User Guide**           | User commands, interfaces, input/output changes, or workflows         |
| **Tutorials**            | Tutorial commands, steps, outputs, error messages, or topics          |
| **Developer Guide**      | Build/test instructions, architecture, development workflows, styles  |
| **Contribution Guidelines** | Contribution processes, code style, commit conventions, issue policies |

---

Thank you for helping keep our documentation accurate and helpful!  
If you have questions about documentation standards, please reach out to the documentation team.

---
