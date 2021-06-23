---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

# Before Submitting Bug Report

在送出 Bug Report 前，請先更新你的 TWSE/TPEX 號碼後，重新測試你的問題會復現後再送出：
Please update your TWSE/TPEX codes, and test your problem again before submitting bug report:

* By CLI

```
$ twstock -U
Start to update codes
Done!
```

* By Python

```
>>> import twstock
>>> twstock.__update_codes()
```


**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Desktop (please complete the following information):**
 - OS: [e.g. iOS]
 - Browser [e.g. chrome, safari]
 - Version [e.g. 22]

**Additional context**
Add any other context about the problem here.
