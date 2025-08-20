# Adding a New Protocol

## Reference Docs

Refer to the following documents whenever creating a new protocol

### canvas_sdk.md
Protocols are built upon the Canvas SDK, documented in canvas_sdk.md

### tellescope_api.md
Protocols handle events and interact with the Tellescope API

## Step-by-Step Instructions for Adding a Protocol
1. Pick an appropriate name that does not exist in the protocols folder
2. Implement the protocol function with clear commenting. Leverage existing utilities if needed and consider adding or updating existing utilities if possible.
3. Review the canvas_sdk.md and tellescope_api.md instructions to make sure the protocol implements these tools correctly. If it does not, refactor the code to fix any issues. Review any utilities to make sure they are incorporated correctly
4. Write thorough test cases of the protcol function by injecting test values and leveraging .env values for interacting with the Tellescope API if needed
5. Run the test cases to ensure they pass and that the output is what we expect

# Adding a New Utility Function

Utilities are Python scripts which live in the utilities folder. These scripts will leverage data types and functions from the Canvas SDK as well as Tellescope API endpoints, so refer to canvas_sdk.md and tellescope_api.md. Each script should represent a single job and export a function that can be re-used within any Protocol. Every script should be well documented with a description at the top, example use cases, and sample code. Example utilities do jobs like:
1. Matching a Canvas Patient to a Tellescope Enduser
2. Matching a Canvas Practitioner to a Tellescope User

At any time when you are developing a new protocol, if you write code that could be more broadly utilized by other protocols, you should create a new utility as part of writing the protocol code. If you're developing a protocol that could rely on an existing utility, please leverage that utility instead of re-writing code. If an existing utility needs to be refactored to be properly utilized in a new protocol, you must make sure that any changes made are backwards-compatible with existing. Test coverage must be written and evaluated for every new utility and every refactor of an existing utility to ensure that it works as expected and that no breaking changes are introduced.

## Step-by-Step Instructions for Adding a new Utility
1. Pick an appropriate name that does not exist in the utilities folder
2. Add a file and start with the description, use cases, and sample usage
3. Implement the utility function with clear commenting and make sure it's available for consumption by 3rd-party scripts
4. Review the canvas_sdk.md and tellescope_api.md instructions to make sure the utility implements these tools correctly. If it does not, refactor the code to fix any issues.
5. Write thorough test cases of the utility function
6. Run the test cases to ensure they pass and that the output is what we expect

## Step-by-Step Instructions for Modifying an Existing Utility
1. If needed, update the description, add example use cases, and add new code samples
3. Modify the existing utility function with clear commenting, making absolutely sure it's backwards-compatible with existing usage
4. Review the canvas_sdk.md and tellescope_api.md instructions to make sure the utility implements these tools correctly. If it does not, refactor the code to fix any issues.
5. Add new test cases of the utility function to cover changes made to the code
6. Run all the test cases to ensure old tests still pass and that new ones do too