# -*- coding: utf-8 -*-
"""Sources Luau integres dans SabreLaser_Combat.rbxlx.

Chaque variable ci-dessous correspond a un Script / LocalScript / ModuleScript
du fichier de place. Aucune troncature : le generateur injecte la chaine entiere.
"""

CONFIG = r'''
--!strict
--[[ ReplicatedStorage/Config/CombatConfig
     Table unique de verite partagee client / serveur. ]]
local Config = {}

-- Endurance
Config.MaxStamina = 100
Config.StaminaRegenPerSecond = 14
Config.AttackCost = 8
Config.BlockHitCost = 5
Config.PerfectParryPenalty = 20

-- Fenetres temporelles (os.clock)
Config.ComboResetTime = 3.0
Config.DeflectResetTime = 3.0
Config.ParryWindow = 0.2
Config.AttackCooldown = 0.44
Config.HitDelay = 0.11
Config.TrailWindow = 0.34
Config.IgniteTime = 0.42
Config.RespawnDelay = 4.0

-- Portee et geometrie
Config.AttackRange = 11.0
Config.BackstabDotThreshold = 0.3
Config.BladeLength = 4.6
Config.BladeRadius = 0.17
Config.LethalDamage = 100
Config.KnockbackImpulse = 62
Config.SpawnPosition = Vector3.new(0, 6, 0)

-- Combos
Config.AttackCount = 10
Config.DeflectCount = 10

-- Rig R15 blocky : 0 = identifiants de maillage R15 cubiques par defaut.
Config.DefaultR15BlockyMeshes = {
	Head = 0, Torso = 0, LeftArm = 0,
	RightArm = 0, LeftLeg = 0, RightLeg = 0,
}
Config.BlockyScales = {
	BodyTypeScale = 0, BodyProportionScale = 0,
	WidthScale = 1, HeightScale = 1,
	DepthScale = 1, HeadScale = 1,
}

-- Plateforme : strictement clavier + souris. Aucune detection gamepad/tactile.
Config.Platform = "PC"
Config.Controls = {
	Draw = "Q", Ignite = "E",
	Attack = "MouseButton1", Block = "MouseButton2",
}

-- Palette chromatique de la lame
Config.Palette = {
	{ name = "Rouge",  color = Color3.fromRGB(255, 55, 55) },
	{ name = "Bleu",   color = Color3.fromRGB(64, 140, 255) },
	{ name = "Vert",   color = Color3.fromRGB(74, 255, 128) },
	{ name = "Violet", color = Color3.fromRGB(178, 76, 255) },
	{ name = "Or",     color = Color3.fromRGB(255, 176, 48) },
	{ name = "Cyan",   color = Color3.fromRGB(64, 238, 255) },
	{ name = "Rose",   color = Color3.fromRGB(255, 110, 196) },
	{ name = "Blanc",  color = Color3.fromRGB(238, 244, 255) },
}
Config.DefaultColor = Color3.fromRGB(64, 140, 255)

-- Sons natifs Roblox (remplacables par n'importe quel rbxassetid).
Config.Sounds = {
	Hum    = "rbxasset://sounds/action_falling.ogg",
	Ignite = "rbxasset://sounds/action_jump.mp3",
	Swing  = "rbxasset://sounds/action_get_up.mp3",
	Clash  = "rbxasset://sounds/impact_water.mp3",
	Draw   = "rbxasset://sounds/action_jump_land.mp3",
}

return Config
'''


INPUT_POLICY = r'''
--!strict
--[[ ReplicatedStorage/Modules/InputPolicy
     Filtre d'entree. Seules les entrees clavier Q/E et souris sont acceptees.
     Les entrees manette et tactiles ne sont ni detectees ni traitees :
     elles tombent simplement dans le cas par defaut. ]]
local Policy = {}

Policy.Platform = "PC"
Policy.Keys = { Q = true, E = true }
Policy.MouseButtons = {
	[Enum.UserInputType.MouseButton1] = true,
	[Enum.UserInputType.MouseButton2] = true,
}

function Policy.IsAllowed(input: InputObject): boolean
	if input.UserInputType == Enum.UserInputType.Keyboard then
		return Policy.Keys[input.KeyCode.Name] == true
	end
	if Policy.MouseButtons[input.UserInputType] then
		return true
	end
	return false
end

function Policy.IsKey(input: InputObject): boolean
	return input.UserInputType == Enum.UserInputType.Keyboard
end

function Policy.IsMouse(input: InputObject, button: Enum.UserInputType): boolean
	return input.UserInputType == button
end

return Policy
'''


SABER_STATE_MACHINE = r'''
--!strict
--[[ ReplicatedStorage/Modules/SaberStateMachine
     Machine a etats stricte du sabre partage.
     Holstered -> Drawn -> Ignited, avec retours controles. ]]
local SM = {}

SM.States = {
	Holstered = "Holstered",
	Drawn = "Drawn",
	Ignited = "Ignited",
}

SM.Actions = {
	Draw = "Draw", Ignite = "Ignite",
	Extinguish = "Extinguish", Holster = "Holster",
}

local TRANSITIONS: { [string]: { [string]: string } } = {
	Holstered = { Draw = "Drawn" },
	Drawn = { Ignite = "Ignited", Holster = "Holstered" },
	Ignited = { Extinguish = "Drawn", Holster = "Holstered" },
}

function SM.IsValid(state: string): boolean
	return TRANSITIONS[state] ~= nil
end

function SM.Next(current: string, action: string): string?
	local branch = TRANSITIONS[current]
	if not branch then return nil end
	return branch[action]
end

function SM.Can(current: string, action: string): boolean
	return SM.Next(current, action) ~= nil
end

function SM.IsIgnited(state: string): boolean
	return state == "Ignited"
end

function SM.HasHiltInHand(state: string): boolean
	return state == "Drawn" or state == "Ignited"
end

return SM
'''


SERVER_STATE = r'''
--!strict
--[[ ServerScriptService/ServerState
     Etat autoritaire partage par tous les scripts serveur (ModuleScript mis en cache). ]]
local State = {}

State.Combat = {} :: { [Player]: any }
State.Sabers = {} :: { [Player]: Model }
State.BladeColors = {} :: { [Player]: Color3 }
State.Spawn = nil :: ((Player) -> boolean)?
State.Version = "1.0.0"

function State.DefaultCombat()
	return {
		stamina = 100,
		guard = false,
		blockStart = nil,
		comboIndex = 1,
		lastAttack = 0,
		deflectIndex = 1,
		lastImpact = 0,
		nextAttack = 0,
		dead = false,
		deployed = false,
		saberState = "Holstered",
		ignited = false,
		color = nil,
	}
end

return State
'''


ANIMATION_LIBRARY = r'''
--!strict
--[[ ReplicatedStorage/Modules/AnimationLibrary
     Genere 10 pistes d'attaque et 10 pistes de deflexion.
     - KeyframeSequences instanciees en Luau (CFrame de poses R15 cubiques).
     - Lecture procedurale par interpolation des Motor6D (aucun asset requis). ]]
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Anim = {}

local JOINTS = {
	"RootJoint", "Waist", "Neck",
	"RightShoulder", "RightElbow", "RightWrist",
	"LeftShoulder", "LeftElbow", "LeftWrist",
	"RightHip", "RightKnee", "RightAnkle",
	"LeftHip", "LeftKnee", "LeftAnkle",
}

local function R(d: number): number
	return math.rad(d)
end

local function P(rx, ry, rz, ox, oy, oz)
	return CFrame.new(ox or 0, oy or 0, oz or 0) * CFrame.Angles(R(rx), R(ry), R(rz))
end

local function idle()
	return {
		RootJoint = P(0, 0, 0), Waist = P(0, 0, 0), Neck = P(0, 0, 0),
		RightShoulder = P(0, 0, 0), RightElbow = P(0, 0, 0),
		LeftShoulder = P(0, 0, 0), LeftElbow = P(0, 0, 0),
		RightHip = P(0, 0, 0), LeftHip = P(0, 0, 0),
	}
end

Anim.AttackTracks = {}
Anim.DeflectTracks = {}

for i = 1, 10 do
	local a = (i - 1) * (math.pi * 2 / 10)
	local sn, cs = math.sin(a), math.cos(a)
	local high = (i % 2 == 0)
	Anim.AttackTracks[i] = {
		Duration = 0.46,
		Keys = {
			{ t = 0.00, pose = idle() },
			{ t = 0.13, pose = {
				Waist = P(0, -22 * sn, 0),
				Neck = P(0, 6 * cs, 0),
				RightShoulder = P(-58 + 12 * cs, 16 * sn, -24 * cs),
				RightElbow = P(0, 0, -38 - 8 * sn),
				RightWrist = P(0, 0, -12 * cs),
				LeftShoulder = P(14 * cs, 0, 22),
				LeftElbow = P(0, 0, 18),
				RootJoint = P(0, -8 * sn, 0),
			} },
			{ t = 0.28, pose = {
				Waist = P(0, 26 * sn, 0),
				Neck = P(0, -7 * cs, 0),
				RightShoulder = P(high and 82 or 68, -20 * cs, 30 * sn),
				RightElbow = P(0, 0, 14 + 8 * cs),
				RightWrist = P(0, 0, 16 * sn),
				LeftShoulder = P(-10 * sn, 0, -20),
				LeftElbow = P(0, 0, -14),
				RootJoint = P(0, 10 * sn, 0),
				RightHip = P(8 * cs, 0, 0), LeftHip = P(-8 * cs, 0, 0),
			} },
			{ t = 0.38, pose = {
				Waist = P(0, 10 * sn, 0),
				RightShoulder = P(38, -8 * cs, 14 * sn),
				RightElbow = P(0, 0, 8),
				LeftShoulder = P(0, 0, -8),
			} },
			{ t = 0.46, pose = idle() },
		},
	}
	Anim.DeflectTracks[i] = {
		Duration = 0.40,
		Keys = {
			{ t = 0.00, pose = idle() },
			{ t = 0.10, pose = {
				Waist = P(0, 18 * sn, 0),
				RightShoulder = P(-30, 12 * cs, 34 * sn),
				RightElbow = P(0, 0, -46),
				RightWrist = P(0, 0, -18),
				LeftShoulder = P(-18, -8 * cs, -20 * sn),
				LeftElbow = P(0, 0, -26),
				Neck = P(0, 8 * sn, 0),
				RootJoint = P(0, 12 * cs, 0),
			} },
			{ t = 0.22, pose = {
				Waist = P(0, -14 * sn, 0),
				RightShoulder = P(-52, -18 * cs, -18 * sn),
				RightElbow = P(0, 0, -22),
				RightWrist = P(0, 0, 12 * cs),
				LeftShoulder = P(-26, 10 * sn, 28 * cs),
				LeftElbow = P(0, 0, -30),
				Neck = P(0, -8 * cs, 0),
			} },
			{ t = 0.32, pose = {
				Waist = P(0, 6 * sn, 0),
				RightShoulder = P(-14, 0, 0),
				RightElbow = P(0, 0, -12),
			} },
			{ t = 0.40, pose = idle() },
		},
	}
end

function Anim.Get(kind: string, index: number)
	local tracks = kind == "Attack" and Anim.AttackTracks or Anim.DeflectTracks
	return tracks[((index - 1) % 10) + 1]
end

-- Instanciation des KeyframeSequences (cote serveur uniquement).
local built = false
function Anim.Build(): Folder
	local root = ReplicatedStorage:FindFirstChild("Animations")
	if not root then
		root = Instance.new("Folder")
		root.Name = "Animations"
		root.Parent = ReplicatedStorage
	end
	if built or not RunService:IsServer() then return root end
	if root:FindFirstChild("Attack_1") then
		built = true
		return root
	end
	built = true
	for kind, tracks in pairs({ Attack = Anim.AttackTracks, Deflect = Anim.DeflectTracks }) do
		for i, track in ipairs(tracks) do
			local seq = Instance.new("KeyframeSequence")
			seq.Name = kind .. "_" .. tostring(i)
			seq.Loop = false
			pcall(function() seq.Priority = Enum.AnimationPriority.Action end)
			for _, key in ipairs(track.Keys) do
				local kf = Instance.new("Keyframe")
				kf.Time = key.t
				kf.Parent = seq
				for jointName, cframe in pairs(key.pose) do
					local pose = Instance.new("Pose")
					pose.Name = jointName
					pose.CFrame = cframe
					pose.Parent = kf
				end
			end
			seq.Parent = root
		end
	end
	return root
end

-- Lecture procedurale : interpolation CFrame des articulations R15.
local active: { [Model]: any } = {}

local function collectJoints(character: Model)
	local joints = {}
	for _, name in ipairs(JOINTS) do
		local motor = character:FindFirstChild(name, true)
		if motor and motor:IsA("Motor6D") then
			joints[name] = { motor = motor, base = motor.C0 }
		end
	end
	return joints
end

local function lerpPose(a, b, alpha)
	local out = {}
	for name, cf in pairs(a) do
		local target = b[name] or CFrame.new()
		out[name] = cf:Lerp(target, alpha)
	end
	for name, cf in pairs(b) do
		if not out[name] then
			out[name] = CFrame.new():Lerp(cf, alpha)
		end
	end
	return out
end

function Anim.Stop(character: Model?)
	if not character then return end
	local current = active[character]
	if not current then return end
	active[character] = nil
	if current.connection then current.connection:Disconnect() end
	for _, entry in pairs(current.joints) do
		if entry.motor and entry.motor.Parent then entry.motor.C0 = entry.base end
	end
end

function Anim.Play(character: Model?, kind: string, index: number, speed: number?)
	if not character then return end
	Anim.Stop(character)
	local track = Anim.Get(kind, index)
	local joints = collectJoints(character)
	if not next(joints) then return end
	local rate = speed or 1
	local start = os.clock()
	local holder = { joints = joints, connection = nil }
	active[character] = holder
	holder.connection = RunService.Heartbeat:Connect(function()
		local elapsed = (os.clock() - start) * rate
		local keys = track.Keys
		local duration = track.Duration
		if elapsed >= duration then
			Anim.Stop(character)
			return
		end
		local lo, hi = keys[1], keys[#keys]
		for k = 1, #keys - 1 do
			if elapsed >= keys[k].t and elapsed < keys[k + 1].t then
				lo, hi = keys[k], keys[k + 1]
				break
			end
		end
		local span = hi.t - lo.t
		local alpha = span > 0.0001 and (elapsed - lo.t) / span or 0
		alpha = math.clamp(alpha, 0, 1)
		-- easing souple (smoothstep)
		alpha = alpha * alpha * (3 - 2 * alpha)
		local pose = lerpPose(lo.pose, hi.pose, alpha)
		for name, entry in pairs(joints) do
			if entry.motor and entry.motor.Parent then
				entry.motor.C0 = entry.base * (pose[name] or CFrame.new())
			end
		end
	end)
end

return Anim
'''


SABER_FACTORY = r'''
--!strict
--[[ ReplicatedStorage/Modules/SaberFactory
     Assemblage, soudure Motor6D, coloration, allumage et trainee du sabre.
     Le modele physique est clone depuis ReplicatedStorage/Assets/SaberTemplate. ]]
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage.Config.CombatConfig)

local Factory = {}
local TEMPLATE = ReplicatedStorage:WaitForChild("Assets"):WaitForChild("SaberTemplate")

local EMITTER_Y = 1.25
local CORE_RADIUS = 0.16
local GLOW_RADIUS = 0.34
-- Part.Shape = Cylinder a son axe le long de X (documentation Roblox actuelle).
-- On applique une rotation fixe de 90 degres autour de Z pour obtenir une
-- lame verticale ; la longueur est donc portee par Size.X.
local BLADE_ROT = CFrame.Angles(0, 0, math.rad(90))

-- Offsets locaux fixes par rapport au centre de la poignee (Handle).
local LOCAL_OFFSETS: { [string]: CFrame } = {
	Grip            = CFrame.new(0, -0.10, 0),
	Pommel          = CFrame.new(0, -0.92, 0),
	EmitterHousing  = CFrame.new(0,  0.95, 0),
	EmitterRing     = CFrame.new(0,  1.12, 0),
	GuardRing       = CFrame.new(0,  1.20, 0),
	SwitchBox       = CFrame.new(0.20, 0.35, 0),
	SwitchLED       = CFrame.new(0.29, 0.35, 0),
	BladeCore       = CFrame.new(0,  3.55, 0) * BLADE_ROT,
	BladeGlow       = CFrame.new(0,  3.55, 0) * BLADE_ROT,
	BladeTip        = CFrame.new(0,  5.88, 0),
}

local HIP_OFFSET = CFrame.new(0.62, -0.35, 0.18) * CFrame.Angles(0, 0, math.rad(18))

local function find(model: Instance?, name: string): Instance?
	return model and model:FindFirstChild(name, true) or nil
end

local function coreC0(len: number): CFrame
	return CFrame.new(0, EMITTER_Y + len / 2, 0) * BLADE_ROT
end

local function tipC0(len: number): CFrame
	return CFrame.new(0, EMITTER_Y + len, 0)
end

function Factory.Create(color: Color3?): Model
	local saber = TEMPLATE:Clone()
	saber.Name = "Saber"
	local handle = find(saber, "Handle")
	-- On remplace les contraintes du template par des Motor6D deterministes.
	for _, d in ipairs(saber:GetDescendants()) do
		if d:IsA("WeldConstraint") or d:IsA("Weld") or d:IsA("Snap") then
			d:Destroy()
		end
	end
	for name, offset in pairs(LOCAL_OFFSETS) do
		local part = find(saber, name)
		if part and part:IsA("BasePart") and handle then
			local motor = find(saber, "Joint_" .. name)
			if not (motor and motor:IsA("Motor6D")) then
				motor = Instance.new("Motor6D")
				motor.Name = "Joint_" .. name
				motor.Parent = handle
			end
			motor.Part0 = handle
			motor.Part1 = part
			motor.C0 = offset
			motor.C1 = CFrame.new()
		end
	end
	for _, d in ipairs(saber:GetDescendants()) do
		if d:IsA("BasePart") then
			d.Anchored = false
			d.CanCollide = false
			d.CastShadow = false
		end
	end
	-- Clone() ne garantit pas le remappage des Ref : on les recable vers les
	-- instances clonees (attachments du Trail, PrimaryPart).
	saber.PrimaryPart = handle
	local trail = find(saber, "BladeTrail")
	if trail and trail:IsA("Trail") then
		local ca0, ca1 = find(saber, "Attach0"), find(saber, "Attach1")
		if ca0 and ca0:IsA("Attachment") then trail.Attachment0 = ca0 end
		if ca1 and ca1:IsA("Attachment") then trail.Attachment1 = ca1 end
	end
	Factory.ApplyColor(saber, color or Config.DefaultColor)
	Factory.SetBlade(saber, false, true)
	Factory.SetLight(saber, false)
	Factory.SetTrail(saber, false)
	return saber
end

function Factory.ApplyColor(saber: Model, color: Color3)
	for _, name in ipairs({ "BladeGlow", "EmitterRing", "BladeTip" }) do
		local p = find(saber, name)
		if p and p:IsA("BasePart") then p.Color = color end
	end
	local light = find(saber, "BladeLight")
	if light and light:IsA("PointLight") then light.Color = color end
	local trail = find(saber, "BladeTrail")
	if trail and trail:IsA("Trail") then trail.Color = ColorSequence.new(color) end
end

function Factory.SetBlade(saber: Model, on: boolean, instant: boolean?)
	local core = find(saber, "BladeCore")
	local glow = find(saber, "BladeGlow")
	local tip = find(saber, "BladeTip")
	local jCore = find(saber, "Joint_BladeCore")
	local jGlow = find(saber, "Joint_BladeGlow")
	local jTip = find(saber, "Joint_BladeTip")
	local len = on and Config.BladeLength or 0.02
	local glowLen = math.max(0.02, len - 0.02)
	local coreTrans = on and 0 or 1
	local glowTrans = on and 0.55 or 1
	local info = TweenInfo.new(Config.IgniteTime, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
	local function apply(obj, props)
		if not obj then return end
		if instant then
			for k, v in pairs(props) do obj[k] = v end
		else
			TweenService:Create(obj, info, props):Play()
		end
	end
	apply(core, { Size = Vector3.new(len, CORE_RADIUS, CORE_RADIUS), Transparency = coreTrans })
	apply(glow, { Size = Vector3.new(glowLen, GLOW_RADIUS, GLOW_RADIUS), Transparency = glowTrans })
	apply(tip, { Transparency = on and 0 or 1 })
	local a0 = find(saber, "Attach0")
	local a1 = find(saber, "Attach1")
	if a0 and a0:IsA("Attachment") then a0.Position = Vector3.new(-len / 2, 0, 0) end
	if a1 and a1:IsA("Attachment") then a1.Position = Vector3.new(len / 2, 0, 0) end
	apply(jCore, { C0 = coreC0(len) })
	apply(jGlow, { C0 = coreC0(glowLen) })
	apply(jTip, { C0 = tipC0(len) })
end

function Factory.SetLight(saber: Model, on: boolean)
	local light = find(saber, "BladeLight")
	if light and light:IsA("PointLight") then light.Enabled = on end
end

function Factory.SetTrail(saber: Model, on: boolean)
	local trail = find(saber, "BladeTrail")
	if trail and trail:IsA("Trail") then trail.Enabled = on end
end

function Factory.TrailWindow(saber: Model, duration: number)
	Factory.SetTrail(saber, true)
	task.delay(duration, function()
		if saber and saber.Parent then Factory.SetTrail(saber, false) end
	end)
end

function Factory.SetHum(saber: Model, on: boolean)
	local hum = find(saber, "Hum")
	if hum and hum:IsA("Sound") then
		if on then
			if not hum.IsPlaying then pcall(function() hum:Play() end) end
		else
			if hum.IsPlaying then pcall(function() hum:Stop() end) end
		end
	end
end

function Factory.PlaySound(saber: Model?, name: string)
	if not saber then return end
	local sound = find(saber, name)
	if sound and sound:IsA("Sound") then
		pcall(function() sound:Play() end)
	end
end

function Factory.GripCFrame(character: Model): CFrame
	local hand = character:FindFirstChild("RightHand")
	local grip = hand and hand:FindFirstChild("RightGripAttachment")
	if grip and grip:IsA("Attachment") then
		return grip.CFrame * CFrame.new(0, -0.12, 0)
	end
	return CFrame.new(0, -1.0, 0)
end

function Factory.Attach(character: Model, saber: Model): Motor6D?
	local lower = character:FindFirstChild("LowerTorso")
	local handle = find(saber, "Handle")
	if not lower or not handle then return nil end
	saber.Parent = character
	local motor = find(saber, "SaberMotor")
	if not (motor and motor:IsA("Motor6D")) then
		motor = Instance.new("Motor6D")
		motor.Name = "SaberMotor"
	end
	motor.Parent = lower
	motor.Part0 = lower
	motor.Part1 = handle
	motor.C0 = HIP_OFFSET
	motor.C1 = CFrame.new()
	return motor
end

function Factory.SetState(character: Model, saber: Model, state: string)
	local motor = character:FindFirstChild("SaberMotor")
	local handle = find(saber, "Handle")
	if not motor or not motor:IsA("Motor6D") or not handle then return end
	local lower = character:FindFirstChild("LowerTorso")
	local hand = character:FindFirstChild("RightHand")
	if state == "Holstered" then
		motor.Part0 = lower
		motor.Parent = lower
		motor.C0 = HIP_OFFSET
		motor.C1 = CFrame.new()
		Factory.SetBlade(saber, false, false)
		Factory.SetLight(saber, false)
		Factory.SetTrail(saber, false)
		Factory.SetHum(saber, false)
		Factory.PlaySound(saber, "Draw")
	elseif state == "Drawn" then
		motor.Part0 = hand
		motor.Parent = hand
		motor.C0 = Factory.GripCFrame(character)
		motor.C1 = CFrame.new()
		Factory.SetBlade(saber, false, false)
		Factory.SetLight(saber, false)
		Factory.SetTrail(saber, false)
		Factory.SetHum(saber, false)
		Factory.PlaySound(saber, "Draw")
	elseif state == "Ignited" then
		motor.Part0 = hand
		motor.Parent = hand
		motor.C0 = Factory.GripCFrame(character)
		motor.C1 = CFrame.new()
		Factory.SetBlade(saber, true, false)
		Factory.SetLight(saber, true)
		Factory.SetHum(saber, true)
		Factory.SetTrail(saber, false)
		Factory.PlaySound(saber, "Ignite")
	end
end

function Factory.BladeSegment(saber: Model?): (Vector3?, Vector3?)
	if not saber then return nil, nil end
	local a = find(saber, "Attach0")
	local b = find(saber, "Attach1")
	if a and a:IsA("Attachment") and b and b:IsA("Attachment") then
		return a.WorldPosition, b.WorldPosition
	end
	return nil, nil
end

return Factory
'''


RIG_SPAWNER = r'''
--!strict
--[[ ServerScriptService/RigSpawner
     Apparition et forçage absolu du rig R15 blocky.
     - Players.CharacterAutoLoads = false : le deploiement est declenche par le menu.
     - PlayerAdded / CharacterAdded / CharacterAppearanceLoaded -> ForceBlocky.
     - HumanoidDescription ecrasee (meshes cubiques = 0) + valeurs d'echelle verrouillees.
     - Creation du sabre partage et soudure sur LowerTorso (etat Holstered). ]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Config = require(ReplicatedStorage.Config.CombatConfig)
local State = require(ServerScriptService.ServerState)
local Factory = require(ReplicatedStorage.Modules.SaberFactory)
local Remotes = ReplicatedStorage.Remotes

local BASE_DESCRIPTION = ReplicatedStorage.Config.BlockyR15Description
local CombatState = Remotes.CombatState
local CombatEvent = Remotes.CombatEvent

Players.CharacterAutoLoads = false

local function setSafe(object: Instance, names: { string }, value: any)
	for _, name in ipairs(names) do
		local ok = pcall(function() object[name] = value end)
		if ok then return true end
	end
	return false
end

local function BuildDescription(): HumanoidDescription
	local d = BASE_DESCRIPTION:Clone()
	for key, value in pairs(Config.DefaultR15BlockyMeshes) do
		setSafe(d, { key }, value)
	end
	setSafe(d, { "BodyTypeScale", "BodyTypeScale" }, 0)
	setSafe(d, { "BodyProportionScale", "ProportionScale" }, 0)
	setSafe(d, { "WidthScale", "BodyWidthScale" }, 1)
	setSafe(d, { "HeightScale", "BodyHeightScale" }, 1)
	setSafe(d, { "DepthScale", "BodyDepthScale" }, 1)
	setSafe(d, { "HeadScale", "BodyHeadScale" }, 1)
	-- vetements / accessoires neutralises
	setSafe(d, { "Shirt", "Pants", "GraphicTShirt", "Face" }, 0)
	for _, accessory in ipairs({
		"HatAccessory", "HairAccessory", "FaceAccessory", "NeckAccessory",
		"ShouldersAccessory", "FrontAccessory", "BackAccessory", "WaistAccessory",
	}) do
		setSafe(d, { accessory }, "")
	end
	return d
end

local function ForceBlocky(character: Model)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid then return end

	-- 1. Verrou direct des NumberValues d'echelle R15.
	local scales = {
		BodyTypeScale = 0, BodyProportionScale = 0,
		BodyWidthScale = 1, BodyHeightScale = 1,
		BodyDepthScale = 1, BodyHeadScale = 1,
	}
	for name, value in pairs(scales) do
		local v = humanoid:FindFirstChild(name)
		if not v then
			v = Instance.new("NumberValue")
			v.Name = name
			v.Parent = humanoid
		end
		v.Value = value
	end

	-- 2. Ecrasement programmatique du HumanoidDescription.
	pcall(function()
		humanoid:ApplyDescription(BuildDescription())
	end)

	-- 3. Purge des accessoires et vetements parasites.
	for _, obj in ipairs(character:GetDescendants()) do
		if obj:IsA("Accessory") or obj:IsA("Shirt") or obj:IsA("Pants")
			or obj:IsA("ShirtGraphic") or obj:IsA("CharacterMesh") then
			obj:Destroy()
		end
	end

	-- 4. Sante normalisee : un coup valide est letal.
	humanoid.MaxHealth = Config.LethalDamage
	if humanoid.Health <= 0 then humanoid.Health = Config.LethalDamage end
end

local function OnDied(player: Player)
	local s = State.Combat[player]
	if not s or s.dead then return end
	s.dead = true
	s.guard = false
	s.blockStart = nil
	CombatState:FireClient(player, "Died", { reason = "lethal" })
	task.delay(Config.RespawnDelay, function()
		if not player.Parent then return end
		local old = State.Sabers[player]
		if old then old:Destroy() end
		State.Sabers[player] = nil
		s.deployed = false
		s.dead = false
		State.Spawn(player)
	end)
end

local function Spawn(player: Player): boolean
	local s = State.Combat[player]
	if not s then
		s = State.DefaultCombat()
		State.Combat[player] = s
	end
	if s.deployed and player.Character then return true end

	local ok, model = pcall(function()
		return Players:CreateHumanoidModelFromDescription(
			BuildDescription(), Enum.HumanoidRigType.R15)
	end)
	if not ok or not model then
		-- Repli sur le chargement standard si l'API n'est pas disponible.
		player:LoadCharacter()
		s.deployed = true
		return true
	end

	model.Name = player.Name
	model.Parent = workspace
	local root = model:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		root.CFrame = CFrame.new(Config.SpawnPosition)
	end
	player.Character = model
	ForceBlocky(model)

	local humanoid = model:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.Died:Connect(function() OnDied(player) end)
	end

	local color = State.BladeColors[player] or Config.DefaultColor
	local saber = Factory.Create(color)
	State.Sabers[player] = saber
	Factory.Attach(model, saber)
	Factory.SetState(model, saber, "Holstered")

	s.deployed = true
	s.dead = false
	s.stamina = Config.MaxStamina
	s.guard = false
	s.blockStart = nil
	s.comboIndex = 1
	s.deflectIndex = 1
	s.lastAttack = 0
	s.lastImpact = 0
	s.saberState = "Holstered"
	s.ignited = false

	CombatState:FireClient(player, "Deployed", {
		state = "Holstered", stamina = s.stamina,
		maxStamina = Config.MaxStamina, platform = Config.Platform,
	})
	CombatEvent:FireAllClients("Deploy", { player = player.Name })
	return true
end

State.Spawn = Spawn

Players.PlayerAdded:Connect(function(player)
	State.Combat[player] = State.DefaultCombat()
	State.BladeColors[player] = Config.DefaultColor
	player.CharacterAdded:Connect(function(character)
		task.defer(function() ForceBlocky(character) end)
	end)
	player.CharacterAppearanceLoaded:Connect(function(character)
		ForceBlocky(character)
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	local saber = State.Sabers[player]
	if saber then saber:Destroy() end
	State.Sabers[player] = nil
	State.BladeColors[player] = nil
	State.Combat[player] = nil
end)

return true
'''


SABER_SERVICE = r'''
--!strict
--[[ ServerScriptService/SaberService
     Gestion autoritaire de la machine a etats du sabre (Draw / Ignite / Holster). ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Config = require(ReplicatedStorage.Config.CombatConfig)
local State = require(ServerScriptService.ServerState)
local SM = require(ReplicatedStorage.Modules.SaberStateMachine)
local Factory = require(ReplicatedStorage.Modules.SaberFactory)
local Remotes = ReplicatedStorage.Remotes

local Action = Remotes.CombatAction
local StateEvent = Remotes.CombatState
local FX = Remotes.CombatEvent

local HANDLED = {
	Draw = true, Ignite = true, Extinguish = true, Holster = true,
}

Action.OnServerEvent:Connect(function(player: Player, action: string)
	if not HANDLED[action] then return end
	local s = State.Combat[player]
	if not s or not s.deployed or s.dead then return end
	local nextState = SM.Next(s.saberState, action)
	if not nextState then return end

	s.saberState = nextState
	s.ignited = SM.IsIgnited(nextState)
	local character = player.Character
	local saber = State.Sabers[player]
	if character and saber then
		Factory.SetState(character, saber, nextState)
	end

	StateEvent:FireClient(player, "SaberState", {
		state = nextState, ignited = s.ignited,
	})
	local color = State.BladeColors[player] or Config.DefaultColor
	FX:FireAllClients("SaberState", {
		player = player.Name, state = nextState,
		r = math.floor(color.R * 255), g = math.floor(color.G * 255),
		b = math.floor(color.B * 255),
	})
end)

return true
'''


COMBAT_SERVER = r'''
--!strict
--[[ ServerScriptService/CombatServer
     Moteur de combat autoritaire : endurance, combos, garde, parade parfaite,
     raycast spatial entre les extremites de la lame, trois conditions letales. ]]
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Config = require(ReplicatedStorage.Config.CombatConfig)
local State = require(ServerScriptService.ServerState)
local Factory = require(ReplicatedStorage.Modules.SaberFactory)
local Anim = require(ReplicatedStorage.Modules.AnimationLibrary)
local SM = require(ReplicatedStorage.Modules.SaberStateMachine)
local Remotes = ReplicatedStorage.Remotes

local Action = Remotes.CombatAction
local StateEvent = Remotes.CombatState
local FX = Remotes.CombatEvent

local BusFolder = ServerStorage:FindFirstChild("CombatBus")
local CombatLog = BusFolder and BusFolder:FindFirstChild("CombatLog")
local function log(kind: string, data: any)
	if CombatLog then
		pcall(function() CombatLog:Fire({ kind = kind, data = data }) end)
	end
end

Anim.Build()

local function now(): number return os.clock() end
local function ensure(p: Player)
	local s = State.Combat[p]
	if not s then s = State.DefaultCombat(); State.Combat[p] = s end
	return s
end
local function hrp(p: Player): BasePart?
	local c = p.Character
	return c and c:FindFirstChild("HumanoidRootPart") or nil
end
local function hum(p: Player): Humanoid?
	local c = p.Character
	return c and c:FindFirstChildOfClass("Humanoid") or nil
end
local function send(p: Player, kind: string, data: any)
	StateEvent:FireClient(p, kind, data)
end
local function broadcast(kind: string, data: any)
	FX:FireAllClients(kind, data)
end

-- Raycast spatial valide par le serveur entre les extremites de la lame.
local function castBlade(origin: Vector3, tip: Vector3, attacker: Player): RaycastResult?
	local direction = tip - origin
	if direction.Magnitude < 0.0001 then return nil end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { attacker.Character }
	params.IgnoreWater = true
	local ok, result = pcall(function()
		return workspace:Raycast(origin, direction, params)
	end)
	if ok then return result end
	return nil
end

local function findTarget(attacker: Player): Player?
	local aroot = hrp(attacker)
	if not aroot then return nil end
	local saber = State.Sabers[attacker]
	local origin, tip = Factory.BladeSegment(saber)
	if not origin or not tip then
		origin = aroot.Position + Vector3.new(0, 2, 0)
		tip = origin + aroot.CFrame.LookVector * Config.AttackRange
	end

	-- 1. Contact direct du segment de lame.
	local hit = castBlade(origin, tip, attacker)
	if hit and hit.Instance then
		local model = hit.Instance:FindFirstAncestorOfClass("Model")
		local candidate = model and Players:GetPlayerFromCharacter(model) or nil
		if candidate and candidate ~= attacker then
			local cs = State.Combat[candidate]
			local ch = hum(candidate)
			if cs and not cs.dead and ch and ch.Health > 0 then return candidate end
		end
	end

	-- 2. Validation spatiale : raycast depuis l'origine de lame vers chaque cible.
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { attacker.Character }
	params.IgnoreWater = true
	local best, bestScore = nil, math.huge
	for _, target in ipairs(Players:GetPlayers()) do
		if target ~= attacker then
			local troot = hrp(target)
			local thum = hum(target)
			local ts = State.Combat[target]
			if troot and thum and thum.Health > 0 and ts and not ts.dead then
				local delta = troot.Position - aroot.Position
				local dist = delta.Magnitude
				local facing = dist > 0.001 and aroot.CFrame.LookVector:Dot(delta / dist) or 0
				local bladeDist = (origin - troot.Position).Magnitude
				if dist <= Config.AttackRange and bladeDist <= Config.AttackRange and facing > 0.10 then
					local direction = troot.Position - origin
					local ray = direction.Magnitude > 0.001
						and workspace:Raycast(origin, direction, params) or nil
					local reached = ray and ray.Instance
						and ray.Instance:IsDescendantOf(target.Character)
					local score = dist - (reached and 5 or 0)
					if score < bestScore then bestScore, best = score, target end
				end
			end
		end
	end
	return best
end

-- Frappe dorsale : produit scalaire des LookVector > 0.3.
local function isBackstab(attacker: Player, target: Player): boolean
	local a, d = hrp(attacker), hrp(target)
	if not a or not d then return false end
	return a.CFrame.LookVector:Dot(d.CFrame.LookVector) > Config.BackstabDotThreshold
end

local function knockback(target: Player, source: Player)
	local r, s = hrp(target), hrp(source)
	if not r or not s then return end
	local delta = r.Position - s.Position
	if delta.Magnitude < 0.001 then delta = s.CFrame.LookVector end
	local flat = Vector3.new(delta.X, 0, delta.Z)
	if flat.Magnitude < 0.001 then flat = Vector3.new(1, 0, 0) end
	local impulse = flat.Unit * Config.KnockbackImpulse * r.AssemblyMass
	pcall(function() r:ApplyImpulse(impulse + Vector3.new(0, r.AssemblyMass * 18, 0)) end)
end

local function kill(attacker: Player, target: Player, reason: string)
	local def = ensure(target)
	if def.dead then return end
	def.dead = true
	def.guard = false
	def.blockStart = nil
	local h = hum(target)
	if h then h:TakeDamage(Config.LethalDamage) end
	send(target, "Hit", { reason = reason, by = attacker.Name })
	send(attacker, "Kill", { victim = target.Name, reason = reason })
	broadcast("Kill", { killer = attacker.Name, victim = target.Name, reason = reason })
	log("Kill", { killer = attacker, victim = target, reason = reason })
	local atk = ensure(attacker)
	atk.stamina = math.min(Config.MaxStamina, atk.stamina + 6)
	send(attacker, "Stamina", atk.stamina)
end

local function resolveHit(attacker: Player, target: Player)
	local atk, def = ensure(attacker), ensure(target)
	if def.dead then return end
	local t = now()

	-- Reinitialisation de la sequence de deflexion apres 3 s sans impact.
	if def.lastImpact > 0 and (t - def.lastImpact) > Config.DeflectResetTime then
		def.deflectIndex = 1
		send(target, "DeflectReset", {})
	end

	local backstab = isBackstab(attacker, target)
	local guarding = def.guard == true and def.blockStart ~= nil
	local perfect = guarding and def.blockStart
		and (t - def.blockStart) <= Config.ParryWindow

	-- Condition letale 3 : frappe dorsale, garde contournee.
	if backstab then
		broadcast("Backstab", { a = attacker.Name, b = target.Name })
		log("Backstab", { attacker = attacker, target = target })
		kill(attacker, target, "backstab")
		return
	end

	-- Condition letale 1 : cible sans garde.
	if not guarding then
		kill(attacker, target, "unguarded")
		return
	end

	-- Parade parfaite : aucun point d'endurance perdu par le defenseur.
	if perfect then
		atk.comboIndex = 1
		atk.lastAttack = 0
		atk.stamina = math.max(0, atk.stamina - Config.PerfectParryPenalty)
		knockback(attacker, target)
		local di = def.deflectIndex
		def.deflectIndex = di % Config.DeflectCount + 1
		def.lastImpact = t
		Anim.Play(target.Character, "Deflect", di)
		if State.Sabers[target] then
			Factory.TrailWindow(State.Sabers[target], 0.24)
			Factory.PlaySound(State.Sabers[target], "Clash")
		end
		send(target, "PerfectParry", { index = di })
		send(attacker, "Parried", { by = target.Name })
		send(attacker, "ComboReset", {})
		send(attacker, "Stamina", atk.stamina)
		broadcast("Clash", { a = attacker.Name, b = target.Name, perfect = true })
		log("PerfectParry", { defender = target, attacker = attacker, index = di })
		return
	end

	-- Blocage classique : -5 endurance + animation de deviation.
	def.stamina = math.max(0, def.stamina - Config.BlockHitCost)
	local di = def.deflectIndex
	def.deflectIndex = di % Config.DeflectCount + 1
	def.lastImpact = t
	Anim.Play(target.Character, "Deflect", di)
	if State.Sabers[target] then
		Factory.TrailWindow(State.Sabers[target], 0.18)
		Factory.PlaySound(State.Sabers[target], "Clash")
	end
	send(target, "Blocked", { index = di, stamina = def.stamina })
	send(target, "Stamina", def.stamina)
	broadcast("Clash", { a = attacker.Name, b = target.Name, perfect = false })
	log("Block", { defender = target, attacker = attacker, index = di })

	-- Condition letale 2 : rupture de garde (endurance epuisee).
	if def.stamina <= 0 then
		def.guard = false
		def.blockStart = nil
		send(target, "Guard", false)
		kill(attacker, target, "guardbreak")
	end
end

Action.OnServerEvent:Connect(function(player: Player, action: string)
	if action ~= "Attack" and action ~= "BlockBegin" and action ~= "BlockEnd" then
		return
	end
	local s = ensure(player)
	if s.dead or not s.deployed then return end
	local t = now()

	if action == "BlockBegin" then
		if not SM.HasHiltInHand(s.saberState) then return end
		if s.guard then return end
		s.guard = true
		s.blockStart = t
		send(player, "Guard", true)
		broadcast("Guard", { player = player.Name, active = true })
		return
	end

	if action == "BlockEnd" then
		s.guard = false
		s.blockStart = nil
		send(player, "Guard", false)
		broadcast("Guard", { player = player.Name, active = false })
		return
	end

	-- Attaque
	if s.saberState ~= "Ignited" then return end
	if s.guard then return end
	if t < s.nextAttack then return end
	if s.stamina < Config.AttackCost then return end

	-- Reinitialisation du combo apres 3 s sans attaque consecutive.
	if s.lastAttack > 0 and (t - s.lastAttack) > Config.ComboResetTime then
		s.comboIndex = 1
		send(player, "ComboReset", {})
	end
	local index = s.comboIndex
	s.comboIndex = index % Config.AttackCount + 1
	s.lastAttack = t
	s.nextAttack = t + Config.AttackCooldown
	s.stamina = math.max(0, s.stamina - Config.AttackCost)

	local saber = State.Sabers[player]
	Anim.Play(player.Character, "Attack", index)
	if saber then
		Factory.TrailWindow(saber, Config.TrailWindow)
		Factory.PlaySound(saber, "Swing")
	end
	send(player, "Combo", { index = index, of = Config.AttackCount })
	send(player, "Stamina", s.stamina)
	broadcast("Swing", { player = player.Name, index = index })

	task.delay(Config.HitDelay, function()
		if not player.Parent then return end
		if ensure(player).dead then return end
		local target = findTarget(player)
		if target then resolveHit(player, target) end
	end)
end)

-- Boucle RunService + estampilles os.clock : regeneration et resets temporels.
local accumulator = 0
RunService.Heartbeat:Connect(function(dt: number)
	accumulator += dt
	if accumulator < 0.1 then return end
	local step = accumulator
	accumulator = 0
	local t = now()
	for player, s in pairs(State.Combat) do
		if player.Parent and s.deployed and not s.dead then
			if s.stamina < Config.MaxStamina then
				s.stamina = math.min(Config.MaxStamina,
					s.stamina + Config.StaminaRegenPerSecond * step)
				send(player, "Stamina", s.stamina)
			end
			if s.comboIndex ~= 1 and s.lastAttack > 0
				and (t - s.lastAttack) > Config.ComboResetTime then
				s.comboIndex = 1
				send(player, "ComboReset", {})
			end
			if s.deflectIndex ~= 1 and s.lastImpact > 0
				and (t - s.lastImpact) > Config.DeflectResetTime then
				s.deflectIndex = 1
				send(player, "DeflectReset", {})
			end
		end
	end
end)

return true
'''


REMOTE_HANDLERS = r'''
--!strict
--[[ ServerScriptService/RemoteHandlers
     RemoteFunction de personnalisation chromatique + deploiement du personnage. ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Config = require(ReplicatedStorage.Config.CombatConfig)
local State = require(ServerScriptService.ServerState)
local Factory = require(ReplicatedStorage.Modules.SaberFactory)
local Remotes = ReplicatedStorage.Remotes

local SetBladeColor = Remotes.SetBladeColor
local DeployCharacter = Remotes.DeployCharacter
local FX = Remotes.CombatEvent

local function clamp255(v: any): number
	if type(v) ~= "number" then return 0 end
	if v ~= v or v == math.huge or v == -math.huge then return 0 end
	return math.clamp(math.floor(v), 0, 255)
end

SetBladeColor.OnServerInvoke = function(player: Player, payload: any)
	local r, g, b
	if type(payload) == "table" then
		r, g, b = clamp255(payload.r), clamp255(payload.g), clamp255(payload.b)
	else
		r, g, b = clamp255(payload), 120, 220
	end
	local color = Color3.fromRGB(r, g, b)
	State.BladeColors[player] = color
	local s = State.Combat[player]
	if s then s.color = color end
	local saber = State.Sabers[player]
	if saber then Factory.ApplyColor(saber, color) end
	FX:FireAllClients("BladeColor", { player = player.Name, r = r, g = g, b = b })
	return true, { r = r, g = g, b = b }
end

DeployCharacter.OnServerInvoke = function(player: Player, payload: any)
	if type(payload) ~= "table" or payload.pc ~= true then
		return false, "plateforme non supportee"
	end
	if payload.platform ~= nil and payload.platform ~= Config.Platform then
		return false, "plateforme non supportee"
	end
	local s = State.Combat[player]
	if s and s.deployed then return true, "deja deploye" end
	if type(State.Spawn) ~= "function" then
		return false, "spawner indisponible"
	end
	local ok, err = pcall(function() State.Spawn(player) end)
	if not ok then return false, tostring(err) end
	return true, "deploye"
end

return true
'''


COMBAT_CLIENT = r'''
--!strict
--[[ StarterPlayer/StarterPlayerScripts/CombatClient
     Saisie PC stricte, synchronisation HUD/FX et effets visuels locaux. ]]
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage.Config.CombatConfig)
local Policy = require(ReplicatedStorage.Modules.InputPolicy)
local Remotes = ReplicatedStorage.Remotes

local Action = Remotes.CombatAction
local StateEvent = Remotes.CombatState
local FX = Remotes.CombatEvent
local player = Players.LocalPlayer

local deployed = false
local drawn = false
local ignited = false

local function fire(action: string, payload: any?)
	Action:FireServer(action, payload)
end

-- Aucun branchement gamepad / tactile : le filtre ignore tout le reste.
UserInputService.InputBegan:Connect(function(input: InputObject, processed: boolean)
	if processed then return end
	if not Policy.IsAllowed(input) then return end
	if input.UserInputType == Enum.UserInputType.Keyboard then
		if input.KeyCode == Enum.KeyCode.Q then
			fire(drawn and "Holster" or "Draw")
		elseif input.KeyCode == Enum.KeyCode.E then
			fire(ignited and "Extinguish" or "Ignite")
		end
	elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
		if deployed then fire("Attack") end
	end
end)

-- Le clic droit est lie via ContextActionService a une priorite superieure a
-- celle de la camera par defaut : la garde ne fait pas pivoter la camera.
ContextActionService:BindActionAtPriority("CombatBlock",
	function(_: string, state: Enum.UserInputState, _input: InputObject)
		if not deployed then return Enum.ContextActionResult.Sink end
		if state == Enum.UserInputState.Begin then
			fire("BlockBegin")
		elseif state == Enum.UserInputState.End then
			fire("BlockEnd")
		end
		return Enum.ContextActionResult.Sink
	end,
	false, 4000, Enum.UserInputType.MouseButton2)

-- Effets visuels : etincelles procedurales, aucune dependance d'asset.
local function sparks(position: Vector3, color: Color3, count: number)
	local anchor = Instance.new("Part")
	anchor.Name = "FXSpark"
	anchor.Size = Vector3.new(0.2, 0.2, 0.2)
	anchor.Transparency = 1
	anchor.CanCollide = false
	anchor.Anchored = true
	anchor.CastShadow = false
	anchor.Position = position
	anchor.Parent = workspace
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = ColorSequence.new(color)
	emitter.Size = NumberSequence.new(0.28, 0)
	emitter.Lifetime = NumberRange.new(0.15, 0.42)
	emitter.Speed = NumberRange.new(5, 13)
	emitter.SpreadAngle = Vector2.new(70, 70)
	emitter.Rate = 0
	emitter.LightEmission = 1
	emitter.Parent = anchor
	emitter:Emit(count or 22)
	task.delay(0.8, function() anchor:Destroy() end)
end

local function positionOf(name: string?): Vector3?
	if not name then return nil end
	local p = Players:FindFirstChild(name)
	local root = p and p.Character
		and p.Character:FindFirstChild("HumanoidRootPart") or nil
	return root and root.Position + Vector3.new(0, 2, 0) or nil
end

FX.OnClientEvent:Connect(function(kind: string, data: any)
	if kind == "Clash" then
		local pos = positionOf(data and data.b)
		if pos then
			sparks(pos, data.perfect and Color3.fromRGB(255, 240, 170)
				or Color3.fromRGB(150, 205, 255), data.perfect and 40 or 20)
		end
	elseif kind == "Kill" then
		local pos = positionOf(data and data.victim)
		if pos then sparks(pos, Color3.fromRGB(255, 90, 90), 55) end
	elseif kind == "Backstab" then
		local pos = positionOf(data and data.b)
		if pos then sparks(pos, Color3.fromRGB(255, 160, 60), 34) end
	elseif kind == "BladeColor" then
		if data and data.player and data.player ~= player.Name then
			local target = Players:FindFirstChild(data.player)
			local saber = target and target.Character
				and target.Character:FindFirstChild("Saber") or nil
			if saber then
				for _, name in ipairs({ "BladeGlow", "EmitterRing", "BladeTip" }) do
					local p = saber:FindFirstChild(name, true)
					if p and p:IsA("BasePart") then
						p.Color = Color3.fromRGB(data.r, data.g, data.b)
					end
				end
			end
		end
	elseif kind == "Trail" then
		local target = data and data.player and Players:FindFirstChild(data.player) or nil
		local saber = target and target.Character
			and target.Character:FindFirstChild("Saber") or nil
		local trail = saber and saber:FindFirstChild("BladeTrail", true) or nil
		if trail and trail:IsA("Trail") then trail.Enabled = data.enabled == true end
	end
end)

StateEvent.OnClientEvent:Connect(function(kind: string, data: any)
	if kind == "Deployed" then
		deployed = true
		drawn = false
		ignited = false
	elseif kind == "SaberState" then
		local state = data and data.state or "Holstered"
		drawn = state ~= "Holstered"
		ignited = state == "Ignited"
	elseif kind == "Died" then
		deployed = false
		drawn = false
		ignited = false
	end
end)

return true
'''


MENU_CONTROLLER = r'''
--!strict
--[[ StarterGui/MainMenu/MenuController
     Menu principal : camera fixe + flou, palette RVB synchronisee serveur,
     bouton de deploiement physique du personnage. ]]
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage.Config.CombatConfig)
local Remotes = ReplicatedStorage.Remotes

local menu = script.Parent
local panel = menu:WaitForChild("Panel")
local preview: Frame = panel:WaitForChild("Preview") :: Frame
local paletteFrame: Frame = panel:WaitForChild("Palette") :: Frame
local deploy: TextButton = panel:WaitForChild("DeployButton") :: TextButton
local status: TextLabel = panel:WaitForChild("Status") :: TextLabel
local rBox: TextBox = panel:WaitForChild("RGBRow"):WaitForChild("RBox") :: TextBox
local gBox: TextBox = panel:WaitForChild("RGBRow"):WaitForChild("GBox") :: TextBox
local bBox: TextBox = panel:WaitForChild("RGBRow"):WaitForChild("BBox") :: TextBox

local SetBladeColor: RemoteFunction = Remotes.SetBladeColor
local DeployCharacter: RemoteFunction = Remotes.DeployCharacter
local StateEvent: RemoteEvent = Remotes.CombatState

local selected = Config.DefaultColor
local deploying = false

local function clamp(v: number): number
	return math.clamp(math.floor(v), 0, 255)
end

local function toRGB(color: Color3): (number, number, number)
	return clamp(color.R * 255), clamp(color.G * 255), clamp(color.B * 255)
end

local function refreshBoxes(color: Color3)
	local r, g, b = toRGB(color)
	rBox.Text = tostring(r)
	gBox.Text = tostring(g)
	bBox.Text = tostring(b)
	preview.BackgroundColor3 = color
	status.Text = "RVB  " .. r .. " / " .. g .. " / " .. b
end

local function pushColor(color: Color3)
	selected = color
	refreshBoxes(color)
	local r, g, b = toRGB(color)
	task.spawn(function()
		local ok = pcall(function()
			return SetBladeColor:InvokeServer({ r = r, g = g, b = b })
		end)
		if not ok then status.Text = "Synchronisation indisponible" end
	end)
end

-- Boutons de palette predefinie.
for i, entry in ipairs(Config.Palette) do
	local button = paletteFrame:FindFirstChild("P" .. tostring(i))
	if button and button:IsA("TextButton") then
		button.BackgroundColor3 = entry.color
		button.MouseButton1Click:Connect(function()
			pushColor(entry.color)
			status.Text = entry.name .. "  —  couleur synchronisee"
		end)
	end
end

local function readRGBBoxes()
	local r = tonumber(rBox.Text) or 0
	local g = tonumber(gBox.Text) or 0
	local b = tonumber(bBox.Text) or 0
	pushColor(Color3.fromRGB(clamp(r), clamp(g), clamp(b)))
end

for _, box in ipairs({ rBox, gBox, bBox }) do
	box.FocusLost:Connect(function() readRGBBoxes() end)
end

-- Camera fixe + flou d'arriere-plan pendant le menu.
local camera = workspace.CurrentCamera
local blur = Lighting:FindFirstChild("MenuBlur")
local function enterMenu()
	camera = workspace.CurrentCamera or camera
	if blur and blur:IsA("BlurEffect") then blur.Enabled = true end
	if camera then
		camera.CameraType = Enum.CameraType.Scriptable
		camera.CFrame = CFrame.new(Vector3.new(0, 20, 46), Vector3.new(0, 3, 0))
	end
	menu.Enabled = true
end

local function leaveMenu()
	deploying = false
	camera = workspace.CurrentCamera or camera
	menu.Enabled = false
	if blur and blur:IsA("BlurEffect") then blur.Enabled = false end
	if camera then camera.CameraType = Enum.CameraType.Custom end
end

deploy.MouseButton1Click:Connect(function()
	if deploying then return end
	deploying = true
	status.Text = "Deploiement en cours..."
	local ok, result = pcall(function()
		return DeployCharacter:InvokeServer({ pc = true, platform = Config.Platform })
	end)
	if ok then
		if result == true then
			leaveMenu()
			return
		end
	end
	deploying = false
	status.Text = "Echec du deploiement — reessayez"
end)

StateEvent.OnClientEvent:Connect(function(kind: string)
	if kind == "Died" then
		status.Text = "Reapparition en cours..."
	elseif kind == "Deployed" then
		leaveMenu()
	end
end)

refreshBoxes(selected)
enterMenu()
return true
'''


HUD_CONTROLLER = r'''
--!strict
--[[ StarterGui/CombatHUD/HUDController
     Jauge d'endurance, combo, etat du sabre, garde, messages de parade. ]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage.Config.CombatConfig)
local Remotes = ReplicatedStorage.Remotes

local hud = script.Parent
local fill: Frame = hud:WaitForChild("StaminaFrame")
	:WaitForChild("BarBack"):WaitForChild("BarFill") :: Frame
local staminaLabel: TextLabel = hud:WaitForChild("StaminaFrame")
	:WaitForChild("StaminaLabel") :: TextLabel
local comboLabel: TextLabel = hud:WaitForChild("ComboFrame"):WaitForChild("ComboLabel") :: TextLabel
local stateLabel: TextLabel = hud:WaitForChild("StateLabel") :: TextLabel
local guardLabel: TextLabel = hud:WaitForChild("GuardLabel") :: TextLabel
local flash: TextLabel = hud:WaitForChild("Flash") :: TextLabel
local feed: TextLabel = hud:WaitForChild("KillFeed") :: TextLabel
local death: Frame = hud:WaitForChild("DeathOverlay") :: Frame
local controls: TextLabel = hud:WaitForChild("Controls") :: TextLabel

local StateEvent: RemoteEvent = Remotes.CombatState
local FX: RemoteEvent = Remotes.CombatEvent

local STATE_TEXT = {
	Holstered = "SABRE  —  RANGE",
	Drawn = "SABRE  —  POIGNEE EN MAIN",
	Ignited = "SABRE  —  LAME ACTIVE",
}

local function setStamina(value: number)
	local pct = math.clamp(value / Config.MaxStamina, 0, 1)
	fill.Size = UDim2.new(pct, 0, 1, 0)
	fill.BackgroundColor3 = pct > 0.5 and Color3.fromRGB(90, 220, 165)
		or (pct > 0.2 and Color3.fromRGB(255, 196, 80) or Color3.fromRGB(255, 86, 86))
	staminaLabel.Text = "ENDURANCE   " .. tostring(math.floor(value))
		.. " / " .. tostring(Config.MaxStamina)
end

local flashToken = 0
local function showFlash(text: string, color: Color3)
	flashToken += 1
	local token = flashToken
	flash.Text = text
	flash.TextColor3 = color
	flash.Visible = true
	task.delay(1.0, function()
		if token == flashToken then flash.Visible = false end
	end)
end

local function showFeed(text: string)
	feed.Text = text
	feed.Visible = true
	task.delay(2.6, function() feed.Visible = false end)
end

controls.Text = "Q  degainer    E  allumer    Clic gauche  attaque    Clic droit  garde"

StateEvent.OnClientEvent:Connect(function(kind: string, data: any)
	if kind == "Deployed" then
		hud.Enabled = true
		death.Visible = false
		comboLabel.Text = "COMBO  1 / 10"
		stateLabel.Text = STATE_TEXT.Holstered
		setStamina(Config.MaxStamina)
		showFlash("DEPLOYE", Color3.fromRGB(150, 220, 255))
	elseif kind == "Stamina" then
		setStamina(tonumber(data) or Config.MaxStamina)
	elseif kind == "Combo" then
		comboLabel.Text = "COMBO  " .. tostring(data.index) .. " / " .. tostring(data.of)
	elseif kind == "ComboReset" then
		comboLabel.Text = "COMBO  1 / 10"
	elseif kind == "DeflectReset" then
		-- sequence de deviations revenue au premier cran
	elseif kind == "SaberState" then
		stateLabel.Text = STATE_TEXT[data.state] or data.state
	elseif kind == "Guard" then
		guardLabel.Text = data and "GARDE  ACTIVE" or ""
	elseif kind == "PerfectParry" then
		showFlash("PARFAITE  !", Color3.fromRGB(255, 238, 150))
	elseif kind == "Parried" then
		showFlash("ATTAQUE PAREE", Color3.fromRGB(255, 140, 140))
	elseif kind == "Blocked" then
		showFlash("BLOQUE", Color3.fromRGB(170, 210, 255))
	elseif kind == "Hit" then
		showFlash("ELIMINE  —  " .. tostring(data.reason), Color3.fromRGB(255, 100, 100))
		death.Visible = true
	elseif kind == "Kill" then
		showFeed("ELIMINATION  —  " .. tostring(data.victim) .. "  (" .. tostring(data.reason) .. ")")
	elseif kind == "Died" then
		death.Visible = true
		guardLabel.Text = ""
	end
end)

FX.OnClientEvent:Connect(function(kind: string, data: any)
	if kind == "Kill" then
		showFeed(tostring(data.killer) .. "  >  " .. tostring(data.victim))
	end
end)

hud.Enabled = false
setStamina(Config.MaxStamina)
return true
'''


ANIMATE_PLACEHOLDER = r'''
--!strict
--[[ StarterCharacterScripts/Animate
     Placeholder volontaire : il empeche Roblox d'injecter son script Animate
     par defaut, lequel ecraserait les C0 pilotes par AnimationLibrary.
     Toutes les animations du jeu sont procedurables (Motor6D + KeyframeSequence). ]]
return nil
'''


COMBAT_LOGGER = r'''
--!strict
--[[ ServerScriptService/CombatLogger
     Statistiques joueur : ecoute le BindableEvent interne CombatBus/CombatLog.
     Alimente un dossier leaderstats replique (Kills, Deaths, Parries, Blocks,
     Backstabs) sans jamais faire confiance au client. ]]
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local bus = ServerStorage:WaitForChild("CombatBus")
local signal: BindableEvent = bus:WaitForChild("CombatLog") :: BindableEvent

local LABELS = { "Kills", "Deaths", "Parries", "Blocks", "Backstabs" }

local function folder(player: Player): Folder
	local ls = player:FindFirstChild("leaderstats")
	if not ls then
		ls = Instance.new("Folder")
		ls.Name = "leaderstats"
		ls.Parent = player
		for _, label in ipairs(LABELS) do
			local v = Instance.new("IntValue")
			v.Name = label
			v.Value = 0
			v.Parent = ls
		end
	end
	return ls :: Folder
end

local function bump(player: any, label: string, amount: number?)
	if not player or not player:IsA("Player") then return end
	local v = folder(player):FindFirstChild(label)
	if v and v:IsA("IntValue") then
		v.Value = math.max(0, v.Value + (amount or 1))
	end
end

Players.PlayerAdded:Connect(function(player) folder(player) end)
for _, player in ipairs(Players:GetPlayers()) do folder(player) end

signal.Event:Connect(function(entry: any)
	if type(entry) ~= "table" then return end
	local kind, d = entry.kind, entry.data
	if type(d) ~= "table" then return end
	if kind == "Kill" then
		bump(d.killer, "Kills")
		bump(d.victim, "Deaths")
		if d.reason == "guardbreak" then bump(d.killer, "Blocks") end
	elseif kind == "PerfectParry" then
		bump(d.defender, "Parries")
	elseif kind == "Block" then
		bump(d.defender, "Blocks")
	elseif kind == "Backstab" then
		bump(d.attacker, "Backstabs")
	end
end)

return true
'''


SPAWN_GUARD = r'''
--!strict
--[[ ServerScriptService/SpawnGuard
     Garantit qu'aucun decor parasite n'apparait dans Workspace :
     surveille les descendants et supprime tout BasePart exterieur a la
     Baseplate native..File d'attente non bloquante. ]]
local Workspace = game:GetService("Workspace")

local allowed: { [Instance]: boolean } = {}
local baseplate = Workspace:FindFirstChild("Baseplate")
if baseplate then allowed[baseplate] = true end

local function isCharacterPart(inst: Instance): boolean
	local model = inst:FindFirstAncestorOfClass("Model")
	if not model then return false end
	return model:FindFirstChildOfClass("Humanoid") ~= nil
end

Workspace.DescendantAdded:Connect(function(inst: Instance)
	if not inst:IsA("BasePart") then return end
	if allowed[inst] or inst:IsA("Terrain") then return end
	if isCharacterPart(inst) then return end
	task.defer(function()
		if inst.Parent then inst:Destroy() end
	end)
end)

return true
'''
