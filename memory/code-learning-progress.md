# Claude Code 源码学习进度

## 学习顺序（按计划v2）
优先级从高到低，依次学习：

| # | 模块 | 源码文件 | 状态 |
|---|------|---------|------|
| 1 | Feature Flag系统 | `src/utils/featureFlags.ts` | ✅ 已完成 |
| 2 | 上下文缓存 | `src/context.ts` | ✅ 已完成 |
| 3 | BaseTool工具体系 | `src/Tool.ts` | ✅ 已完成 |
| 4 | 工具注册表 | `src/tools.ts` | ✅ 已完成 |
| 5 | Agent上下文隔离 | `src/utils/agentContext.ts` | ✅ 已完成 |
| 6 | AgentTool嵌套 | `src/tools/AgentTool/AgentTool.tsx` | ✅ 已完成 |
| 7 | Bash权限分类器 | `src/tools/BashTool/bashPermissions.ts` | ✅ 已完成 |
| 8 | Hooks系统 | `src/utils/hooks.ts` | ✅ 已完成 |
| 9 | SkillTool | `src/tools/SkillTool/SkillTool.ts` | ✅ 已完成 |
| 10 | MCP系统 | `src/services/mcp/client.ts` | ✅ 已完成 |
| 11 | 命令注册表 | `src/commands.ts` | ✅ 已完成（SkillRegistry已覆盖）|
| 12 | 状态管理 | `src/state/AppState.tsx` | ✅ 已完成 |

## 当前进度
- 当前模块：第4轮学习进行中
- 第1轮：1-12全部完成
- 第2轮（17:04-18:05）：8项全部完成
- 第3轮（18:05起）：系统集成+实用化
  - ✅ 历史记录系统（trading_history.py）
  - ✅ 盘中监控API链打通
  - ✅ 5个交易cron状态推送
- 第4轮（21:06起）：实用化模块
  - ✅ cost-tracker.ts → cost_tracker.py（成本追踪系统）
  - ✅ stream.ts → Stream类（async流式迭代器）

## 新增模块
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 13 | 历史记录系统 | `src/history.ts` | trading_history.py | ✅ |
| 14 | 成本追踪 | `src/cost-tracker.ts` | cost_tracker.py | ✅ |
| 15 | Async Stream | `src/utils/stream.ts` | agent_tool.py Stream类 | ✅ |
| 16 | Prompt模板 | `src/utils/argumentSubstitution.ts` | prompt_template.py | ✅ |
| 17 | 重试+限流 | `rateLimitMessages.ts` | retry.py | ✅ |
| 18 | TTL缓存 | `src/utils/memoize.ts` | memoize.py | ✅ |
| 19 | 上下文分析 | `src/utils/contextAnalysis.ts` | context_analyzer.py | ✅ |
| 20 | HTTP预热 | `src/utils/apiPreconnect.ts` | preconnect.py | ✅ |
| 21 | 优雅退出 | `cleanupRegistry.ts` | cleanup.py | ✅ |
| 22 | 数据Diff | `diff.ts` | diff.py | ✅ |
| 23 | 文件监控 | `fileChangedWatcher.ts` | file_watcher.py | ✅ |
| 24 | 结构化日志 | `internalLogging.ts` | logger.py | ✅ |
| 25 | MCP客户端 | `src/services/mcp/client.ts` | mcp_client.py | ✅ |
| 26 | 异步Stream | `src/utils/stream.ts` | stream.py | ✅ |
| 27 | 代理客户端 | `upstreamproxy.ts` | proxy.py | ✅ |
| 28 | 事件分析 | `src/services/analytics/index.ts` | analytics.py | ✅ |
| 29 | 错误处理 | `src/utils/errors.ts` | errors.py | ✅ |
| 30 | 事件信号 | `src/utils/signal.ts` | signal.py | ✅ |
| 31 | 任务队列 | `src/utils/sdkEventQueue.ts` | task_queue.py | ✅ |
| 32 | 缓存系统 | `src/utils/fileReadCache.ts` | cache.py | ✅ |
| 33 | 文件锁 | `src/utils/lockfile.ts` | lockfile.py | ✅ |
| 34 | 环境工具 | `src/utils/env.ts` | env.py | ✅ |
| 35 | ID生成器 | `src/utils/uuid.ts` | id.py | ✅ |
| 36 | 格式化工具 | `src/utils/format.ts` | format.py | ✅ |
| 37 | 文本截断 | `src/utils/truncate.ts` | truncate.py | ✅ |
| 38 | JSON处理 | `src/utils/json.ts` | json_utils.py | ✅ |
| 39 | 数据验证器 | `src/utils/settings/validation.ts` | validators.py | ✅ |
| 40 | 异步工具 | async patterns | async_utils.py | ✅ |
| 41 | Cron调度 | `src/utils/cron.ts` | cron.py | ✅ |
| 42 | 限流器 | rate limiting | rate_limit.py | ✅ |
| 43 | Abort控制器 | `src/utils/abortController.ts` | abort.py | ✅ |
| 44 | 睡眠工具 | `src/utils/sleep.ts` | sleep.py | ✅ |
| 45 | 数组工具 | `src/utils/array.ts` | array_utils.py | ✅ |
| 46 | 字符串工具 | `src/utils/stringUtils.ts` | string_utils.py | ✅ |
| 47 | 路径工具 | `src/utils/path.ts` | path_utils.py | ✅ |
| 48 | 文件工具 | `src/utils/file.ts` | file_utils.py | ✅ |
| 49 | 调试工具 | `src/utils/debug.ts` | debug_utils.py | ✅ |
| 50 | YAML处理 | `src/utils/yaml.ts` | yaml_utils.py | ✅ |
| 51 | 进程工具 | `src/utils/process.ts` | process_utils.py | ✅ |
| 52 | 命令查找 | `src/utils/which.ts` | which.py | ✅ |
| 53 | XDG目录 | `src/utils/xdg.ts` | xdg.py | ✅ |
| 54 | 随机单词 | `src/utils/words.ts` | words.py | ✅ |
| 55 | 哈希工具 | `src/utils/hash.ts` | hash_utils.py | ✅ |
| 56 | HTTP工具 | `src/utils/http.ts` | http_utils.py | ✅ |
| 57 | 加密工具 | `src/services/oauth/crypto.ts` | crypto_utils.py | ✅ |
| 58 | 活动管理 | `src/utils/activityManager.ts` | activity_manager.py | ✅ |
| 59 | 提示词模板 | prompt system | prompt.py | ✅ |

## 更新规则
每次学习完一个模块，在此文件更新"当前模块"为下一个

## 第60批（2026-04-04 08:30）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 60 | 顾问系统 | `src/utils/advisor.ts` | advisor.py | ✅ |
| 61 | 智能会话搜索 | `src/utils/agenticSessionSearch.ts` | agentic_search.py | ✅ |
| 62 | 上下文分析 | `src/utils/analyzeContext.ts` | context_analyzer.py | ✅ |

## 第61批（2026-04-04 08:35）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 63 | 附件系统 | `src/utils/attachments.ts` | attachments.py | ✅ |

## 第62批（2026-04-04 08:40）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 64 | 边查询API | `src/utils/sideQuery.ts` | side_query.py | ✅ |
| 65 | 慢操作日志 | `src/utils/slowOperations.ts` | slow_operations.py | ✅ |

## 第63批（2026-04-04 08:43）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 66 | 会话存储 | `src/utils/sessionStorage.ts` | session_storage.py | ✅ |
| 67 | 文件历史 | `src/utils/fileHistory.ts` | file_history.py | ✅ |

## 第64批（2026-04-04 08:50）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 68 | 工作目录 | `src/utils/cwd.ts` | cwd.py | ✅ |
| 69 | 环境变量 | `src/utils/envUtils.ts` | env_utils.py | ✅ |
| 70 | 路径工具 | `src/utils/path.ts` | path_utils.py | ✅ |

## 第65批（2026-04-04 08:53）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 71 | 格式化工具 | `src/utils/format.ts` | format.py | ✅ |
| 72 | 字符串工具 | `src/utils/stringUtils.ts` | string_utils.py | ✅ |

## 第66批（2026-04-04 08:56）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 73 | JSON工具 | `src/utils/json.ts` | json_utils.py | ✅ |
| 74 | 日志工具 | `src/utils/log.ts` | log.py | ✅ |

## 第67批（2026-04-04 09:00）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 75 | 缓存工具 | `src/utils/memoize.ts` | memoize.py | ✅ |
| 76 | 中断控制器 | `src/utils/abortController.ts` | abort_controller.py | ✅ |

## 第68批（2026-04-04 09:03）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 77 | 命令查找 | `src/utils/which.ts` | which.py | ✅ |
| 78 | 进程执行 | `src/utils/execFileNoThrow.ts` | exec_utils.py | ✅ |

## 第69批（2026-04-04 09:06）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 79 | 显示标签 | `src/utils/displayTags.ts` | display_tags.py | ✅ |
| 80 | 数组工具 | `src/utils/array.ts` | array_utils.py | ✅ |

## 第70批（2026-04-04 09:10）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 81 | 二进制检查 | `src/utils/binaryCheck.ts` | binary_check.py | ✅ |
| 82 | UUID工具 | `src/utils/uuid.ts` | uuid_utils.py | ✅ |

## 第71批（2026-04-04 09:13）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 83 | 清理注册表 | `src/utils/cleanupRegistry.ts` | cleanup_registry.py | ✅ |
| 84 | 错误类 | `src/utils/errors.ts` | errors.py | ✅ |

## 第72批（2026-04-04 09:16）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 85 | Beta特性管理 | `src/utils/betas.ts` | betas.py | ✅ |

## 第73批（2026-04-04 09:20）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 86 | API提供者 | `src/utils/model/providers.ts` | providers.py | ✅ |
| 87 | 平台检测 | `src/utils/platform.ts` | platform.py | ✅ |

## 第74批（2026-04-04 09:22）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 88 | 缓存路径 | `src/utils/cachePaths.ts` | cache_paths.py | ✅ |

## 第75批（2026-04-04 09:24）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 89 | 哈希工具 | `src/utils/hash.ts` | hash_utils.py | ✅ |

## 第76批（2026-04-04 09:26）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 90 | 字符串截断 | `src/utils/truncate.ts` | truncate.py | ✅ |

## 第77批（2026-04-04 09:28）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 91 | 环形缓冲区 | `src/utils/CircularBuffer.ts` | circular_buffer.py | ✅ |

## 第78批（2026-04-04 09:30）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 92 | 归属文本 | `src/utils/attribution.ts` | attribution.py | ✅ |

## 第79批（2026-04-04 09:33）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 93 | 活动管理器 | `src/utils/activityManager.ts` | activity_manager.py | ✅ |

## 第80批（2026-04-04 09:35）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 94 | Agent团队开关 | `src/utils/agentSwarmsEnabled.ts` | agent_swarms.py | ✅ |
| 95 | 参数替换 | `src/utils/argumentSubstitution.ts` | argument_substitution.py | ✅ |

## 第81批（2026-04-04 09:37）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 96 | 终端录制 | `src/utils/asciicast.ts` | asciicast.py | ✅ |

## 第82批（2026-04-04 09:40）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 97 | 缓冲写入器 | `src/utils/bufferedWriter.ts` | buffered_writer.py | ✅ |

## 第83批（2026-04-04 09:42）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 98 | 调试日志 | `src/utils/debug.ts` | debug.py | ✅ |

## 第84批（2026-04-04 09:45）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 99 | Agent标识 | `src/utils/agentId.ts` | agent_id.py | ✅ |
| 100 | Claude提示协议 | `src/utils/claudeCodeHints.ts` | claude_code_hints.py | ✅ |

## 第85批（2026-04-04 09:48）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 101 | Signal信号 | `src/utils/signal.ts` | signal.py | ✅ |
| 102 | CA证书 | `src/utils/caCerts.ts` | ca_certs.py | ✅ |

## 第86批（2026-04-04 09:50）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 103 | AWS工具 | `src/utils/aws.ts` | aws_utils.py | ✅ |
| 104 | Claude桌面配置 | `src/utils/claudeDesktop.ts` | claude_desktop.py | ✅ |
