/** @jsx h */
/// <reference no-default-lib="true"/>
/// <reference lib="dom" />
/// <reference lib="dom.asynciterable" />
/// <reference lib="deno.ns" />
import { h, ssr } from "https://crux.land/nanossr@0.0.5";
import { router } from "https://crux.land/router@0.0.12";
import { serve } from "https://deno.land/std@0.150.0/http/server.ts";

serve(router(
  {
    "/": async (_req, context) => {
      const ip = (context.remoteAddr as Deno.NetAddr).hostname;
      const res = await fetch("http://ip-api.com/json/" + ip);
      const data: APIData = await res.json();
      return ssr(() => <Landing {...data} />);
    },
    "/bagels/:id": (_req, _context, matches) => {
      return ssr(() => <Bagel id={matches.id} />);
    },
    "/search": (req) => {
      const search = new URL(req.url).searchParams.get("search");
      return ssr(() => <Search search={search ?? ""} />);
    },
  },
));

interface APIData {
  country: string;
  city: string;
  timezone: string;
}

function Landing({
  country,
  city,
  timezone,
}: APIData) {
  return (
    <div class="min-h-screen p-4 flex gap-12 flex-col items-center justify-center">
      <h1 class="text-2xl font-semibold">
        Welcome to Bagel Search
      </h1>
      <p class="max-w-prose">
        It's currently {new Date().toLocaleString("en-US", {
          dateStyle: "full",
          timeStyle: "medium",
          timeZone: timezone,
        })} in {city}, {country}—the perfect time and place to look up a bagel.
      </p>
      <a
        href="/search"
        class="px-4 py-2.5 rounded-md font-medium leading-none bg-gray-100 hover:bg-gray-200"
      >
        Click here to search for bagels
      </a>
    </div>
  );
}

const bagels = [
  {
    name: "Salmon Bagel",
    price: 5.39,
    image:
      "https://images.unsplash.com/photo-1592767049184-0fda840ae4e7?w=1080",
    description:
      "There is no better feeling than sinking your teeth into smoked salmon, briny capers, and cream cheese.",
  },
  {
    name: "Cream Cheese Bagel",
    price: 2.49,
    image:
      "https://images.unsplash.com/photo-1585841393012-e4ded4a6e2d0?w=1080",
    description:
      "The original bagel. Its simplicity is nothing to scoff at. The real ones know.",
  },
  {
    name: "Bacon and Rucola Bagel",
    price: 4.19,
    image:
      "https://images.unsplash.com/photo-1603712469481-e25f0bdb63aa?w=1080",
    description:
      "A hearty, yet healthy(-ish?) breakfast bagel. The spiciness from the rucola cut through the savoriness of the bacon.",
  },
  {
    name: "Egg and Ham Bagel",
    price: 3.79,
    image:
      "https://images.unsplash.com/photo-1605661479369-a8859129827b?w=1080",
    description:
      "The classic breakfast sandwich. Or lunch sandwich. Or even dinner sandwich.",
  },
  {
    name: "Jam Bagel",
    price: 3.00,
    image:
      "https://images.unsplash.com/photo-1579821401035-450188d514da?w=1080",
    description:
      "For those with a sweet tooth, the sticky deliciousness of jam with the doughy chewiness of the bagel is a match made in heaven.",
  },
  {
    name: "Bagel Sandwich with Egg, Ham, Tomato, Lettuce & Mayo",
    price: 6.00,
    image:
      "https://images.unsplash.com/photo-1627308595325-182f10f20126?w=1080",
    description:
      "Sometimes you want all your favorite things between two bagels. This crisp, fresh sandwich will fill you up with delicious goodness.",
  },
];

function Bagel({ id }: { id: string }) {
  const name = id.replaceAll("-", " ");
  const bagel = bagels.find((bagel) =>
    bagel.name.toLowerCase() === name.toLowerCase()
  );

  if (bagel === undefined) {
    return (
      <div>
        The bagel '{name}' does not exist.
      </div>
    );
  }

  return (
    <div class="min-h-screen p-4 flex flex-col items-center justify-center">
      <div class="w-3/4 lg:w-1/4">
        <div class="w-full bg-gray-200 rounded-lg overflow-hidden">
          <img
            src={bagel.image}
            class="w-full object-center object-cover"
            alt={bagel.name}
          />
        </div>
        <div class="mt-3 flex items-center justify-between">
          <h1 class="font-semibold">{bagel.name}</h1>
          <p class="text-lg font-medium text-gray-900">
            ${bagel.price.toFixed(2)}
          </p>
        </div>
        <p class="mt-1 text-gray-600">
          {bagel.description}
        </p>
        <div class="mt-3 flex items-center justify-between">
          <div><a href="/" class="underline text-blue-500">Home</a></div>
          <div><a href="/search" class="underline text-blue-500">Back to Search</a></div>
        </div>
      </div>
    </div>
  );
}

function Search({ search }: { search: string }) {
  const foundBagels = bagels.filter((bagel) =>
    bagel.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <form
      method="get"
      class="min-h-screen p-4 flex gap-8 flex-col items-center justify-center"
    >
      <input
        type="text"
        name="search"
        value={search}
        class="h-10 w-96 px-4 py-3 bg-gray-100 rounded-md leading-4 placeholder:text-gray-400"
        placeholder="Search and press enter..."
      />
      <output name="result" for="search" class="w-10/12 lg:w-1/2">
        <ul class="space-y-2">
          {foundBagels.length > 0 &&
            foundBagels.map((bagel) => (
              <li class="hover:bg-gray-100 p-1.5 rounded-md">
                <a href={`/bagels/${bagel.name.replaceAll(" ", "-")}`}>
                  <div class="font-semibold">{bagel.name}</div>
                  <div class="text-sm text-gray-500">{bagel.description}</div>
                </a>
              </li>
            ))}
          <li>
            {foundBagels.length === 0 &&
              <div>No results found. Try again.</div>
            }
          </li>
        </ul>
      </output>
    </form>
  );
}