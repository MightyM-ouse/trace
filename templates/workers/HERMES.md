# Optional Runtime Worker Adapter

This template describes an optional local/runtime worker pattern. It is not a mandatory TRACE dependency.

Default status: inactive.

Activation requires a Product Owner-approved capability-lab task that defines:

- isolated runtime;
- explicit tools and writable paths;
- default-deny policy gate;
- audit-before-effect behavior;
- evidence and handoff requirements;
- independent review.

An activated runtime worker may act only inside its task envelope. It must not self-activate, self-enable tools, mutate memory silently, use credentials, execute external actions, write outside assigned paths, push to `main`, merge, or represent a test result as product acceptance.

