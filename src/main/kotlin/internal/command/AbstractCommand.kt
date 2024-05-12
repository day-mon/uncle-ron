package org.github.daymon.internal.command

import dev.minn.jda.ktx.util.SLF4J
import net.dv8tion.jda.api.Permission
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.commands.build.CommandData
import net.dv8tion.jda.api.interactions.commands.build.Commands
import net.dv8tion.jda.api.interactions.commands.build.SubcommandGroupData
import java.util.*

abstract class AbstractCommand {
    abstract val id: Int
    abstract val name: String
    abstract val description: String
    abstract val memberPermissions: EnumSet<Permission>
    abstract val selfPermissions: EnumSet<Permission>
    abstract val children: List<SubCommand>
    abstract val options: List<CommandOptionData<*>>
    abstract val deferredReplyEnabled: Boolean
    private val logger by SLF4J


    val commandData: CommandData
        get() {
            val slashCommand = Commands.slash(
                name.lowercase(),
                description
            )
            val command = this as Command

            if (command.group.isNotEmpty()) {
                slashCommand.addSubcommandGroups(
                    command.group.map {
                        SubcommandGroupData(
                        it.key, "This ${it.key}'s"
                    ).addSubcommands(it.value.map { cmd -> cmd.subCommandData })
                    }
                )
            }

            if (children.isNotEmpty()) {
                slashCommand.addSubcommands(
                    children.map { it.subCommandData }
                )
            } else {
                slashCommand.addOptions(
                    options.map { it.asOptionData() }
                )
            }

            return slashCommand
        }

    suspend fun process(event: CommandEvent) {
        if (!event.hasMemberPermissions(memberPermissions)) {
            event.replyMessage("You do not have the required permissions to use this command.")
            return
        }
        if (!event.hasSelfPermissions(selfPermissions)) {
            event.replyMessage("I do not have the required permissions to use this command.")
            return
        }

        logger.info("${event.user.name} executed command $name")

        onExecuteSuspend(event)
    }

    open suspend fun onExecuteSuspend(event: CommandEvent)
    {
        event.replyMessage("This command is not implemented yet.")
        throw NotImplementedError("Execution for $name has not implemented ")
    }

    open suspend fun onAutoCompleteSuspend(event: CommandAutoCompleteInteractionEvent)
    {
        throw NotImplementedError("Autocomplete for $name has not implemented ")
    }
}