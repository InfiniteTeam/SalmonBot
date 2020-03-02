def PageControl(reaction, user, msg, allpage, perpage, nowpage):
    page = nowpage
    if reaction.emoji == '⏹':
        return None, msg.clear_reactions()
    elif reaction.emoji == '▶':
        if page < allpage:
            return page + 1, msg.remove_reaction('▶', user)
        else:
            return page, msg.remove_reaction('▶', user)
    elif reaction.emoji == '◀':
        if page > 0: 
            return page - 1, msg.remove_reaction('◀', user)
        else:
            return page, msg.remove_reaction('◀', user)
    elif reaction.emoji == '⏩':
        if page < allpage-perpage:
            return page + perpage, msg.remove_reaction('⏩', user)
        elif page == allpage:
            return page, msg.remove_reaction('⏩', user)
        else:
            return allpage, msg.remove_reaction('⏩', user)
    elif reaction.emoji == '⏪':
        if page > perpage:
            return page - perpage, msg.remove_reaction('⏪', user)
        elif page == 0:
            return page, msg.remove_reaction('⏪', user)
        else:
            page = 0
            return page, msg.remove_reaction('⏪', user)