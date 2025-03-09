open System.Text.RegularExpressions
open System.IO

let intlCharacters = 
    File.ReadAllLines "replace_chars.txt"
    |> Seq.filter (fun x -> not (System.String.IsNullOrWhiteSpace x))
    |> Seq.map (fun x -> x.Trim())
    |> Seq.toArray

let pattern = 
    intlCharacters
    |> String.concat ""
    |> sprintf "[%s]"

let script = File.ReadAllText "script.rb"
let newScript = Regex.Replace(script, pattern, fun m -> $"@u%d{int m.Value[0]}")
File.WriteAllText("script.rb", newScript)
