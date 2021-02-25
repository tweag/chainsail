export const floor = (number) => {
  if (number > 0) {
    let i = 0;
    while (i + 1 < number) {
      i += 1;
    }
    return i;
  } else {
    let i = 0;
    while (i - 1 > number) {
      i -= 1;
    }
    return i;
  }
};
