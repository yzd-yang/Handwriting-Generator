module.exports = {
  branches: ["master"], // 与实际主分支名一致
  plugins: [
    "@semantic-release/commit-analyzer", // 分析提交信息，确定版本更新类型（major/minor/patch）
    "@semantic-release/release-notes-generator", // 根据提交生成 changelog
    "@semantic-release/changelog", // 更新 CHANGELOG.md
    [
      "@semantic-release/github", // 发布到 GitHub，生成 Release
      {
        assets: ["dist/**/*.{js,css}", "docs/**/*"], // 可发布的构建文件
      },
    ],
    [
      "@semantic-release/git", // 推送更新后的版本和 changelog 文件
      {
        assets: ["CHANGELOG.md", "package.json"],
        message: "chore(release): ${nextRelease.version} [skip ci]",
      },
    ],
  ],
};
