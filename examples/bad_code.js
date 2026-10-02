// 与 bad_code.py 对应的 JavaScript 版本，用于演示「非 Python 语言」的审查路径。
// 这段代码里埋了几个典型问题：
//   1. div 函数没有处理除零（返回 Infinity）
//   2. processList 里 push 的是 result[i]（应为 items[i]），结果是 NaN
//   3. 大量使用 var、用 == 做判断

function divide(a, b) {
  return a / b;
}

function processList(items) {
  var result = [];
  for (var i = 0; i < items.length; i++) {
    if (items[i] != null) {
      result.push(result[i] * 2);
    }
  }
  return result;
}

console.log(divide(10, 0));
console.log(processList([1, 2, 3]));
