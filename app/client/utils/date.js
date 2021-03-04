import moment from 'moment';

export const dateFormatter = (d) => {
  if (d) return moment(d).format('d MMM hh:mm');
  else return '---';
};
