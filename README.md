# minetest-urbit-relay
Connects an urbit ship with a Minetest server, sending chat messages between the two. Originally built for the Urchat server, (starring the righteous Uqbar gang)

## Architecture
Urbit ship subscribes to group, and puts new messages in a queue. Python server takes those messages and returns them to the minetest mod, which polls the HTTP GET endpoint every second. If the mod gets a response back, it prints the messages in chat. If the server has a Minetest chat, it sends that on to the HTTP server, which triggers the Urbit ship to send that message in the group.


### Future state
Ideally you would be able to do this by having the minetest mod talk directly to Urbit, but that's difficult because I suck at hoon. I'm also not sure how minetset security works, and if I'd want to store my moon's +code in the mod.


## Credits: 
+ Architecture + some code taken from MIT licensed Minetest<->Discord bridge (discordmt)[https://github.com/archfan7411/discordmt]
+ Variation of Urbit<->Discord bridge taken from ~midsum-salrux's (faux-legacy)[https://github.com/midsum-salrux/faux-legacy]


