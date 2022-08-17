local http = minetest.request_http_api()
local settings = minetest.settings

local port = settings:get('urbit.port') or 8092
local timeout = 10

urbit = {}

urbit.text_colorization = settings:get('urbit.text_color') or '#ffffff'

urbit.registered_on_messages = {}

urbit.register_on_message = function(func)
    table.insert(urbit.registered_on_messages, func)
end   

urbit.chat_send_all = minetest.chat_send_all

urbit.handle_response = function(response)
    local data = response.data
    if data == '' or data == nil then
        return
    end
    local data = minetest.parse_json(response.data)
    if not data then
        return
    end
    if data.messages then
        for _, message in pairs(data.messages) do
            for _, func in pairs(urbit.registered_on_messages) do
                func(message.author, message.content)
            end
            local msg = ('<%s@urbit> %s'):format(message.author, message.content)
            urbit.chat_send_all(minetest.colorize(urbit.text_colorization, msg))
            -- minetest.log('action', '[minetest-urbit-relay] Message: '..msg)
        end
    end
end


urbit.send = function(message, id)
    local data = {
        type = 'URBIT-RELAY-MESSAGE',
        content = minetest.strip_colors(message)
    }
    if id then
        data['context'] = id
    end
    http.fetch({
        url = 'localhost:'..tostring(port),
        timeout = timeout,
        post_data = minetest.write_json(data)
    }, function(_) end)
end

minetest.chat_send_all = function(message)
    urbit.chat_send_all(message)
    -- urbit.send(message) --uncomment if you want all server messages to be relayed like the /me chats
end

minetest.register_on_chat_message(function(name, message)
    urbit.send(('**<%s>** %s'):format(name, message))
end)


-- need to be continuously polling the relay server for new messages
local timer = 0
minetest.register_globalstep(function(dtime)
    if dtime then
        timer = timer + dtime
        if timer > 0.2 then
            http.fetch({
                url = 'localhost:'..tostring(port),
                timeout = timeout,
                post_data = minetest.write_json({
                    type = 'URBIT-REQUEST-DATA'
                })
            }, urbit.handle_response)
            timer = 0
        end
    end
end)

minetest.register_on_shutdown(function()
    urbit.send('**Server shutting down...**')
end)

urbit.send('**Server started!**')
minetest.log('info', 'Loaded minetest-urbit-relay mod')
