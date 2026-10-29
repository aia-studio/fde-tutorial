# NOTICE — 内容来源与许可

## 本教程正文

`content/` 目录下的全部课程内容为**原创中文讲解**，基于对 Python 官方文档
（docs.python.org）的学习与理解重新组织而成：

- 只做概念引用与官方链接跳转（每课 `doc_refs`）；
- 不逐字翻译、不大段摘录官方文档；
- 代码示例为教学目的独立编写。

官方文档的版权归 Python Software Foundation，适用
[PSF License](https://docs.python.org/3/license.html)。本项目的引用方式
（原创讲解 + 指向原文的链接）符合该许可的署名要求。

## 第三方组件

本项目**零第三方依赖**：后端仅使用 Python 标准库（`http.server`、`subprocess`、
`tomllib`、`dis` 等），前端为原生 ES Module（无框架、无构建、无 CDN）。

## 教程中提到的第三方名称

课程正文为教学目的提及 numpy、pydantic、FastAPI 等项目名称与特性，
它们归各自作者所有，本教程不包含、不分发其代码。

## 教程自身代码

`app.py`、`build.py`、`tutorial/`、`web/`、`tests/` 为本项目原创代码，
随仓库分发（许可由仓库根 LICENSE 决定，如未提供则保留所有权利）。
