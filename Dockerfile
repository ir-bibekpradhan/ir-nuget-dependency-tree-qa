FROM mcr.microsoft.com/dotnet/sdk:8.0

ARG PROJECT=scenarios/04-shared-dependency/SharedDependency.csproj

WORKDIR /src
COPY . .

RUN dotnet restore "$PROJECT" --locked-mode

CMD ["dotnet", "--info"]
