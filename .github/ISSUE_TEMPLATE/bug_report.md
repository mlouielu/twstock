---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

# Frequently Asked Questions

## Q: realtime.get not working

A: Check if you query the data in trading hours. Realtime query is no support outside the trading hours.
A: 請先檢查目前是否在台股交易時段，本功能無法在非交易時段使用。

## Q: Can not query specific symbol

A: Please update your TWSE/TPEX codes (method below).
A: 請先嘗試更新 TWSE/TPEX codes (方法在下方)。

## Q: Unable to query in all methods

A: Check if you reach query limitation, you may want to use proxies, or reduce your query frequency.
A: 請檢查你是否請求資料過快，你可以嘗試使用 proxies，或是降低請求資料的頻率。

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


---

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
