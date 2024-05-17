package org.github.daymon.commands.main.info


import dev.minn.jda.ktx.messages.Embed

import net.dv8tion.jda.api.JDAInfo
import org.github.daymon.ext.toHumanTime
import org.github.daymon.internal.command.Command
import org.github.daymon.internal.command.CommandEvent
import java.lang.management.ManagementFactory

class Info : Command(
    name = "BotInfo",
    description = "Shows bot information",
)
{


    override suspend fun onExecuteSuspend(event: CommandEvent)
    {
        val jda = event.jda
        val runtime = Runtime.getRuntime()

        event.replyEmbed(
            Embed {
                title = "Uncle Ron Information"

                field {
                    name = "JVM Version"
                    value = "${System.getProperty("java.version")} by ${System.getProperty("java.vendor")}"
                    inline = false
                }

                field {
                    name = "JDA Version"
                    value = JDAInfo.VERSION
                    inline = false
                }

                field {
                    name = "Host OS"
                    value = "${System.getProperty("os.name")}  (${System.getProperty("os.arch")}) on v${System.getProperty("os.version")}"
                    inline = false
                }

                field {
                    name = "Memory Usage"
                    value =  "${(runtime.totalMemory() - runtime.freeMemory() shr 20)} MB /  ${runtime.maxMemory() shr 20} MB"
                    inline = false
                }

                field {
                    name = "Thead Count"
                    value = ManagementFactory.getThreadMXBean().threadCount.toString()
                    inline = false
                }

                field {
                    name = "Guild Count"
                    value = jda.guildCache.size().toString()
                    inline = false
                }

                field {
                    name = "User Count"
                    value = jda.guilds.stream().mapToInt { it.memberCount }.sum().toString()
                    inline = false
                }

                field {
                    name = "Uptime"
                    value = ManagementFactory.getRuntimeMXBean().uptime.toBigDecimal().toHumanTime()
                    inline = false
                }
            }
        )
    }
}