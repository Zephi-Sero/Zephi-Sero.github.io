local init
do
  local component_invoke = component.invoke
  local function invoke(address, method, ...)
    local result = table.pack(pcall(component_invoke, address, method, ...))
    if not result[1] then
      return nil, result[2]
    else
      return table.unpack(result, 2, result.n)
    end
  end
  local function beep(freq)
    computer.beep(freq)
  end

  do
    local screen = component.list("screen")()
    local gpu = component.list("gpu")()
    local keyboard = component.list("keyboard")()[1]
    local eeprom = component.list("eeprom")()

    if gpu and screen then
      invoke(gpu, "bind", screen)
    else
      if gpu and not screen then
        error("Could not find screen!")
        computer.beep("..")
      else
        error("Could not find GPU")
        computer.beep(".-")
      end
    end
    local function haltfunc()
      -- none
    end
    local x=1
    local y=1
    local w, h = invoke(gpu,"getResolution")
    invoke(gpu,"setBackground",0x909090)
    invoke(gpu,"setForeground",0x73EF81)
    local function print(str)
      invoke(gpu,"set",x,y,str)
      x = x + string.len(str)
      if x >= w then
        y = y + math.floor(x/w)
        x = x % w
      end
    end
    local function newline()
      x = 1
      y = y + 1
    end
    local function println(str)
      print(str)
      newline()
    end
    local function put(str,x,y)
      invoke(gpu,"set",x,y,str)
    end
    local function clearscr()
      for y=1, h do
        put(string.rep(" ",w),1,y)
      end
      x=1
      y=1
    end
    clearscr()
    println("ZephBIOS started successfully!")
    for k,v in component.list() do
      println("Found component type " .. v .. " id " .. k)
    end
    computer.getBootAddress = function()
      return invoke(eeprom,"getData")
    end
    computer.setBootAddress = function(addr)
      invoke(eeprom, "setData", addr)
    end
    local function searchFS()
      for fs in component.list("filesystem") do
        println("Found drive " .. fs)
        if invoke(fs,"exists","/boot.sig") then
          local fstream,reason = invoke(fs,"open","/boot.sig")
          if fstream ~= nil then
            local str, err = invoke(fs,"read",fstream,9)
            invoke(fstream,"close")
            if str == "ZephiOwO" then
              println("Found boot signature on drive " .. fs .. " (/boot.sig)")
              local fstream,reason = invoke(fs,"open","/init.lua")
              if fstream ~= nil then
                local buffer = ""
                repeat
                  data = invoke(fs,"read",fstream,math.huge)
                  buffer = buffer .. (data or "")
                until data == nil
                println("Found init.lua on drive " .. fs .. " (/init.lua)")
                computer.setBootAddress(fs)
                return buffer,load(buffer,"=init")
              else
                println("Did not find init.lua on drive " .. fs)
              end
            else
              println("Did not find valid boot signature on drive " .. fs)
            end
          end
        end
      end
    end
    computer.pullSignal(1.0)
    buf, initlua = searchFS()
    if not buf then
      println("No boot signature found on drives. Halting...")
    else
      initlua()
    end
    repeat
      computer.pullSignal(0.1)
    until invoke(keyboard, "isKeyDown", "enter")
  end
end
