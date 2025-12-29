var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddOpenApi();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

// app.UseHttpsRedirection();

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

    return new 
    { 
        Message = $"Found {nth}th prime number", 
        Result = prime, 
        DurationMs = durationMs,
        Platform = ".NET" 
    };
})
.WithName("GetHeavyComputation");

 app.MapGet("/io", async () =>
{
    // Simulate I/O delay
    await Task.Delay(100);
    return new { Message = "I/O Operation Complete", Platform = ".NET" };
})
.WithName("GetIOBound");

app.Run();