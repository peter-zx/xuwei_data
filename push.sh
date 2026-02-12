#!/bin/bash

# Git推送脚本 - Excel数据处理器
# 功能：提交代码并推送到codebuddy01分支

echo "========================================="
echo " Excel数据处理器 - 代码推送脚本"
echo "========================================="
echo ""

# 检查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo "✓ 工作区干净，没有需要提交的更改"
    echo ""
    echo "直接推送到远程分支..."
    git push origin codebuddy01 --force
else
    echo "发现未提交的更改，准备提交..."
    echo ""

    # 显示更改状态
    git status --short
    echo ""

    # 输入提交信息
    if [ -z "$1" ]; then
        echo "请输入提交信息（留空使用默认）:"
        read commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="更新代码 - $(date '+%Y-%m-%d %H:%M')"
        fi
    else
        commit_msg="$1"
    fi

    echo ""
    echo "提交信息: $commit_msg"
    echo ""

    # 添加所有更改
    git add -A

    # 提交
    git commit -m "$commit_msg"

    echo "✓ 代码已提交"
    echo ""

    # 推送
    echo "正在推送到远程分支 codebuddy01..."
    git push origin codebuddy01 --force
fi

echo ""
echo "✓ 推送完成！"
echo "========================================="
