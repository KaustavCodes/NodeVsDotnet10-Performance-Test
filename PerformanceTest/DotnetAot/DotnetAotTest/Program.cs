using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Http.HttpResults;

var builder = WebApplication.CreateSlimBuilder(args);

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonSerializerContext.Default);
});

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();


var app = builder.Build();
// Set Kestrel to listen on port 5600
app.Urls.Add("http://localhost:5600");

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

// Function to calculate nth prime number (CPU intensive)
int GetNthPrime(int n)
{
    int count = 0;
    int num = 2;
    while (count < n)
    {
        bool isPrime = true;
        for (int i = 2; i <= Math.Sqrt(num); i++)
        {
            if (num % i == 0)
            {
                isPrime = false;
                break;
            }
        }
        if (isPrime)
        {
            count++;
        }
        if (count < n)
        {
            num++;
        }
    }
    return num;
}

app.MapGet("/heavy", async () =>
{
    var start = DateTime.UtcNow;
    var nth = 20000; // Calculate 20,000th prime

    // Offload to thread pool to allow checking multi-threaded performance
    var prime = await Task.Run(() => GetNthPrime(nth));

    var end = DateTime.UtcNow;
    var durationMs = (end - start).TotalMilliseconds;

    return new HeavyResponse(
        $"Found {nth}th prime number",
        prime,
        durationMs,
        ".NET"
    );
})
.WithName("GetHeavyComputation");

app.MapGet("/io", async () =>
{
    // Simulate I/O delay
    await Task.Delay(100);
    return new IoResponse("I/O Operation Complete", ".NET AOT");
})
.WithName("GetIOBound");

app.Run();

public record HeavyResponse(String Message, int Result, double DurationMs, String Platform);
public record IoResponse(String Message, string Platform);

[JsonSerializable(typeof(HeavyResponse[]))]
[JsonSerializable(typeof(IoResponse[]))]
internal partial class AppJsonSerializerContext : JsonSerializerContext
{

}