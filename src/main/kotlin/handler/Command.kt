package org.github.daymon.handler

import dev.minn.jda.ktx.events.CoroutineEventListener
import dev.minn.jda.ktx.events.getDefaultScope
import dev.minn.jda.ktx.util.SLF4J
import kotlinx.coroutines.launch
import net.dv8tion.jda.api.events.GenericEvent
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.events.interaction.command.SlashCommandInteractionEvent
import net.dv8tion.jda.api.events.session.ReadyEvent
import org.github.daymon.commands.main.`fun`.Ask
import org.github.daymon.commands.main.info.Info
import org.github.daymon.commands.main.misc.Leetify
import org.github.daymon.commands.main.misc.Ping
import org.github.daymon.commands.main.misc.Search
import org.github.daymon.commands.main.money.Economy
import org.github.daymon.commands.main.money.Security
import org.github.daymon.commands.sub.money.SecurityPrice
import org.github.daymon.internal.command.AbstractCommand
import org.github.daymon.internal.command.Command
import org.github.daymon.internal.command.CommandEvent
import kotlin.math.log


object CommandHandler : CoroutineEventListener {

    private val scope = getDefaultScope()
    private val logger by SLF4J
    private val commands: MutableMap<String, Command> = mutableMapOf()

    fun registerCommands(event: ReadyEvent) {
        val commandsUpdate = event.jda.updateCommands()
        val commandList = arrayOf(
            Ping(),
            Security(),
            Ask(),
            Economy(),
            Leetify(),
            Info(),
            Search()
        )

        commandList.forEach { cmd ->
            commandsUpdate.addCommands(cmd.commandData)
            commands[cmd.name.lowercase()] = cmd
        }

        commandsUpdate.queue()
        logger.info("{} commands have been successfully registered", commands.size)

    }

    override suspend fun onEvent(event: GenericEvent)
    {
        when (event) {
            is SlashCommandInteractionEvent -> handleSlashCommand(event)
            is CommandAutoCompleteInteractionEvent -> handleAutoComplete(event)
            is ReadyEvent -> registerCommands(event)
        }
    }


    fun handleSlashCommand(event: SlashCommandInteractionEvent)
    {
        if (!event.isFromGuild) return event.reply("This command must be sent from a guild").queue()

        val cmdName = event.name
        val group = event.subcommandGroup
        val subCommand = event.subcommandName
        val command = commands[cmdName]
            ?: return event.reply("$cmdName command has not been found :(").queue()


        when
        {
            group != null -> scope.launch {
                val sub = command.group[group]?.find { it.name ==  subCommand }
                    ?: return@launch  event.reply("${command.name} $group $subCommand has not been found").queue()

                if (sub.deferredReplyEnabled)
                    event.deferReply().queue()

                sub.process(
                    CommandEvent(command = sub, slashEvent = event)
                )
            }
            subCommand != null -> scope.launch {
                val sub = command.children.find { it.name == event.subcommandName }
                    ?: return@launch event.reply("${command.name} $subCommand has not been found").queue()

                if (sub.deferredReplyEnabled)
                    event.deferReply().queue()

                sub.process(
                    CommandEvent(command = sub, slashEvent = event)
                )

            }
            else -> scope.launch {
                if (command.deferredReplyEnabled)
                    event.deferReply().queue()

                command.process(
                    CommandEvent(command = command, slashEvent = event)
                )
            }
        }
    }

    fun handleAutoComplete(event: CommandAutoCompleteInteractionEvent)
    {
        if (!event.isFromGuild) return
        val command = event.name
        val group = event.subcommandGroup
        val sub = event.subcommandName
        val commandF = commands[command]
            ?: return logger.error("$command could not be found")

        when {
            group != null -> scope.launch {
                val subC = commandF.group[group]?.find { it.name ==  sub }
                    ?: return@launch logger.error("${commandF.name} $group $sub could not be found")
                subC.onAutoCompleteSuspend(event)
            }
            sub != null -> scope.launch {
                val subCommand = commandF.children.find { it.name == event.subcommandName }
                    ?: return@launch logger.error("${commandF.name} $sub could not be found")
                subCommand.onAutoCompleteSuspend(event)
            }
            else -> scope.launch {
                commandF.onAutoCompleteSuspend(event)
            }
        }
    }




}