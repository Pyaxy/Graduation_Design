#!/bin/bash

# 运行测试并收集覆盖率数据
coverage run --source='.' manage.py test course.tests subject.tests accounts.tests

# 生成覆盖率报告
coverage report

# 生成HTML格式的详细报告
coverage html

echo "测试覆盖率报告已生成，请查看 coverage_html/index.html" 